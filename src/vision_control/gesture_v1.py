"""Measured hand features and deterministic Gesture Hand v1 arbitration."""
import math
from dataclasses import dataclass
from .gestures import _geometry, _joint_angle, finger_states, is_closed_fist, thumb_state
from .types import distance


@dataclass(frozen=True)
class Features:
    palm: tuple
    index: tuple
    scale: float
    spread: float
    radius: float
    angle: float
    fingers: tuple
    thumb: str
    pinch: bool
    fist: bool
    symbol: str
    cluster: bool
    thumb_extended: bool = False
    pinch_ratio: float = 1.
    middle_pinch_ratio: float = 1.


def features(hand, size, cfg, calibration=None):
    if hand is None or hand.confidence < .7:
        return None
    p = _geometry(hand, size)
    if p is None:
        return None
    scale = distance(p[0], p[9])
    if scale < .025 or any(distance(p[a], p[b]) > scale * 2.5
                           for a, b in ((5, 8), (9, 12), (13, 16), (17, 20), (0, 4))):
        return None
    states = finger_states(hand, size)
    thumb = thumb_state(hand, size)
    if calibration is not None:
        states = (calibration.finger(hand, 8, size) == 'extended',
                  calibration.finger(hand, 12, size) == 'extended', *states[2:])
        thumb = calibration.thumb(hand, size)
    tips = (8, 12, 16, 20)
    spread = sum(distance(p[a], p[b]) for a, b in zip(tips, tips[1:])) / (3 * scale)
    pinch = distance(p[4], p[8]) / scale < .28
    fist = is_closed_fist(hand, size) and thumb != 'open'
    cluster = max(distance(p[a], p[b]) for a in (4, *tips) for b in (4, *tips)) / scale < .65
    symbol = ''
    if pinch and all(states[1:]):
        symbol = 'ok'
    elif states == (True, True, False, False) and distance(p[8], p[12]) / scale > cfg['close_spread']:
        symbol = 'victory'
    elif not any(states) and thumb == 'open':
        dx, dy = p[4][0] - p[2][0], p[4][1] - p[2][1]
        if abs(dy) > abs(dx):
            symbol = 'thumbs_up' if dy < 0 else 'thumbs_down'
    palm = tuple(sum(hand.landmarks[i][a] for i in (0, 5, 9, 13, 17)) / 5 for a in (0, 1))
    return Features(palm, hand.landmarks[8][:2], scale, spread,
                    sum(distance(p[i], p[9]) for i in tips) / (4 * scale),
                    math.atan2(p[5][1] - p[17][1], p[5][0] - p[17][0]),
                    states, thumb, pinch, fist, symbol, cluster,
                    (_joint_angle(p[2], p[3], p[4]) or 0) >= 150 and
                    distance(p[4], p[0]) > distance(p[3], p[0]) + .02 * scale,
                    distance(hand.landmarks[4], hand.landmarks[8]) /
                    max(distance(hand.landmarks[0], hand.landmarks[9]), .001),
                    distance(hand.landmarks[4], hand.landmarks[12]) /
                    max(distance(hand.landmarks[0], hand.landmarks[9]), .001))


class Stability:
    def __init__(self):
        self.name = ''; self.since = 0.; self.fired = False

    def update(self, name, now, delay):
        if name != self.name:
            self.name, self.since, self.fired = name, now, False
        progress = min(1., max(0., (now - self.since) / delay)) if name else 0.
        ready = bool(name) and progress >= 1 and not self.fired
        if ready:
            self.fired = True
        return ready, progress


class SecondHand:
    def __init__(self, adapter, cfg):
        self.adapter, self.cfg = adapter, cfg
        self.gate = Stability(); self.held = set(); self.status = 'Idle'; self.progress = 0.

    def release(self):
        from .input_adapter import release_each
        def up(key):
            self.adapter.key_up(key); self.held.discard(key)
        release_each([lambda key=k: up(key) for k in tuple(self.held)])

    def reset(self):
        self.release(); self.gate = Stability(); self.progress = 0.; self.status = 'Idle'

    def update(self, f, now, enabled):
        if f is None or not enabled:
            self.reset(); self.status = 'No hand' if enabled else 'Off'; return
        modifier = ('ctrl' if f.fist else 'alt' if f.pinch else
                    'shift' if all(f.fingers) and f.thumb_extended and f.thumb != 'open' and
                    f.spread <= self.cfg['close_spread'] else '')
        count = 0
        patterns = [(True, False, False, False), (True, True, False, False),
                    (True, True, True, False), (True, True, True, True)]
        if f.fingers in patterns:
            count = patterns.index(f.fingers) + 1
            if count == 4 and f.thumb == 'open':
                count = 5 if f.spread >= self.cfg['wide_spread'] else 0
        binding = self.cfg['bindings'].get(str(count), {}) if not modifier else {}
        name = modifier or (f'finger_{count}' if binding else '')
        if name != self.gate.name:
            self.release()
        ready, self.progress = self.gate.update(name, now, self.cfg['modifier_seconds'] if modifier else self.cfg['pose_seconds'])
        self.status = f'{name} {self.progress:.0%}' if name else 'Idle'
        if not ready:
            return
        keys = [modifier] if modifier else binding['keys'].split('+')
        if modifier or binding['type'] == 'hold':
            for key in keys:
                self.held.add(key); self.adapter.key_down(key)
        else:
            self.adapter.perform('+'.join(keys))


class PrimaryHand:
    """Consumes special gestures; False delegates to the existing mouse controller."""
    def __init__(self, adapter, cfg):
        self.adapter, self.cfg = adapter, cfg
        self.two_hands = cfg['two_hands']
        self.reset()

    def reset(self):
        self.gate = Stability(); self.switch_gate = Stability()
        self.mode = ''; self.anchor = None; self.axis = None; self.remainder = 0.
        self.status = ''; self.progress = 0.; self.previous = None
        self.last_step = 0.

    def update(self, f, now, mouse):
        self.progress = 0.
        if f is None:
            self.reset(); mouse.release_all(); self.status = 'Tracking unclear'; return True
        if self.previous:
            old, stamp = self.previous
            dt = now - stamp
            if dt <= 0:
                return True
            if dt > .15:
                self.reset(); mouse.release_all()
            elif math.dist(f.index, old.index) > .12 and math.dist(f.palm, old.palm) < .035:
                self.previous = (f, now)
                mouse.release_all(); self.mode = ''; self.gate = Stability()
                self.status = 'Landmark jump'; return True
        self.previous = (f, now)
        if mouse.left_down or mouse.right_down or mouse.middle_down:
            self.mode = ''; self.gate = Stability(); self.switch_gate = Stability()
            return False  # Existing drag owns the sequence, including release.
        if self.cfg['volume'] and f.fist and not any(f.fingers):
            mouse.thumb_control.predict_enabled = False
            mouse.thumb_control.clicks.reset()
            mouse.thumb_control.pending_at = mouse.thumb_control.ready_at = None
            mouse.thumb_control.right_contact.armed = False
            mouse.thumb_control.right_contact.latched = True
            self.switch_gate = Stability()
            if self.mode != 'volume':
                self.mode = ''
                ready, self.progress = self.gate.update('volume', now, self.cfg['pose_seconds'])
                self.status = f'Volume ready {self.progress:.0%}'
                if ready:
                    self.mode = 'volume'; self.anchor = f; self.last_step = now
            else:
                delta = f.palm[0] - self.anchor.palm[0]
                if abs(delta) >= .04 and now - self.last_step >= .12:
                    self.adapter.perform('volume_up' if delta > 0 else 'volume_down')
                    self.anchor = f; self.last_step = now
                self.status = 'volume'
            return True
        if self.mode == 'volume' or self.gate.name == 'volume':
            self.mode = ''; self.gate = Stability(); self.anchor = None
        if mouse.profile.pointer_mode in {'palm', 'thumb_lock'}:
            opened = mouse.profile.thresholds.get('pinch_open_ratio', .45)
            contact = mouse.thumb_control.right_contact
            contact.observe_separated(f.middle_pinch_ratio > opened and f.pinch_ratio > opened)
            if f.middle_pinch_ratio <= opened or contact.latched:
                # Contact owns approach, click and hold before motion/symbol gestures.
                self.mode = ''; self.gate = Stability(); self.switch_gate = Stability()
                return False
        clicks = mouse.thumb_control.clicks
        if mouse.profile.pointer_mode == 'palm' and f.thumb == 'open':
            clicks.observe_extended('open', {
                'index': 'extended' if f.fingers[0] else 'unknown',
                'middle': 'extended' if f.fingers[1] else 'unknown',
            }, now)
            if clicks.cycle_active:
                self.mode = ''; self.gate = Stability()
                return False
        # Volume must not swallow the separation that prepares a pinch drag.
        opened = getattr(mouse.profile, 'thresholds', {}).get('pinch_open_ratio', .45)
        if not f.pinch and f.pinch_ratio > opened:
            mouse.thumb_control.ready_at = now
        if self.cfg['fist_switch'] and f.fist:
            ready, self.progress = self.switch_gate.update('switch', now, 3.)
            mouse.release_all(); self.gate = Stability(); self.mode = ''
            if ready:
                self.two_hands = not self.two_hands
            self.status = f'Two hands {"On" if self.two_hands else "Off"} · {self.progress:.0%}'
            return True
        self.switch_gate.update('', now, 3.)
        candidate = self.candidate(f)
        if self.mode:
            return self.advance(f, candidate, now, mouse)
        ready, self.progress = self.gate.update(candidate, now,
            self.cfg['symbol_seconds'] if candidate.startswith('symbol:') else self.cfg['pose_seconds'])
        if not candidate:
            self.status = ''; return False
        if candidate == 'scroll':
            # A stationary open thumb is still the user's click lock.
            # Reserve scrolling only after directional movement is observed.
            if ready:
                self.mode = candidate; self.anchor = f; self.axis = None; self.remainder = 0.
            if mouse.profile.pointer_mode == 'palm':
                mouse.thumb_control.predict_enabled = False
                self.status = f'Scroll ready {self.progress:.0%}'
                return True
            return False
        mouse.thumb_control.predict_enabled = False
        mouse.thumb_control.clicks.clear_cycle()
        mouse.thumb_control.pending_at = None
        self.status = f'{candidate} {self.progress:.0%}'
        if ready:
            self.mode = candidate; self.anchor = f; self.axis = None; self.remainder = 0.; self.last_step = now
            if candidate.startswith('symbol:'):
                self.adapter.perform(self.cfg['symbols'][candidate.split(':')[1]])
        return True

    def candidate(self, f):
        if f.symbol and self.cfg['symbols'].get(f.symbol):
            return 'symbol:' + f.symbol
        if self.cfg['scroll'] and f.thumb == 'open' and all(f.fingers) and f.spread <= self.cfg['close_spread']:
            return 'scroll'
        if self.cfg['volume'] and f.fist and not any(f.fingers):
            return 'volume'
        return ''

    def advance(self, f, candidate, now, mouse):
        mouse.thumb_control.predict_enabled = False
        if self.mode.startswith('symbol:'):
            keep = candidate == self.mode
        elif self.mode == 'scroll':
            keep = candidate == 'scroll'
            if not keep and self.axis is None:
                self.mode = ''; self.gate = Stability()
                return False
            if keep:
                dx, dy = f.palm[0] - self.anchor.palm[0], f.palm[1] - self.anchor.palm[1]
                if self.axis is None and max(abs(dx), abs(dy)) >= .018:
                    self.axis = 0 if abs(dx) > abs(dy) * 1.3 else 1 if abs(dy) > abs(dx) * 1.3 else None
                if self.axis is not None:
                    amount = dx if self.axis == 0 else -dy
                    self.remainder += amount * self.cfg['scroll_speed'] * (-1 if self.cfg['reverse_scroll'] else 1)
                    step = max(-5, min(5, int(self.remainder)))
                    if step:
                        self.adapter.scroll_xy(step if self.axis == 0 else 0, step if self.axis == 1 else 0)
                        self.remainder -= step
                    self.anchor = f
                    mouse.thumb_control.clicks.clear_cycle()
                    mouse.thumb_control.pending_at = None
                else:
                    if mouse.profile.pointer_mode == 'palm':
                        self.status = 'Scroll ready'
                        return True
                    return False
        self.status = self.mode
        if not keep:
            self.mode = ''; self.gate = Stability(); mouse.release_all()
            self.status = 'Gesture released'
        return True
