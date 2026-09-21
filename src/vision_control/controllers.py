import math
import time

from .calibration import MouseCalibration
from .gestures import classify_static, classify_mouse_pose, finger_states, pinch, finger_extended, is_closed_fist, thumb_state
from .input_adapter import InputAdapter, release_each
from .monitors import EdgeDwellSwitcher, MonitorLayout, ScreenRegion
from .profile import Profile
from .types import HandObservation


class GestureController:
    def __init__(self, adapter: InputAdapter, profile: Profile):
        self.adapter, self.profile = adapter, profile
        self.current = "none"
        self.on_count = self.off_count = 0
        self.held: set[str] = set()

    def update(self, hand: HandObservation | None, frame_size=(640, 480)) -> str:
        if not hand or hand.confidence < self.profile.thresholds.get("gesture_confidence", .7):
            self._release(); return "none"
        gesture, _ = classify_static(hand, frame_size)
        binding = self.profile.bindings.get(gesture)
        if gesture != self.current and self.held:
            self._release()
        if not binding:
            self._release(); self.current = gesture; return gesture
        if gesture == self.current:
            self.on_count += 1
        else:
            self.current, self.on_count, self.off_count = gesture, 1, 0
        if self.on_count >= int(self.profile.thresholds.get("gesture_on_frames", 3)):
            if binding.action_type == "press":
                if self.on_count == int(self.profile.thresholds.get("gesture_on_frames", 3)):
                    if len(binding.keys) == 1:
                        self.adapter.key_press(binding.keys[0])
                    else:
                        pressed = []
                        try:
                            for key in binding.keys:
                                pressed.append(key)
                                self.adapter.key_down(key)
                        finally:
                            release_each([lambda key=key: self.adapter.key_up(key)
                                          for key in reversed(pressed)])
            else:
                for key in binding.keys:
                    if key not in self.held: self.adapter.key_down(key); self.held.add(key)
        return gesture

    def _release(self):
        self.current = "none"
        self.on_count = 0
        def release(key):
            self.adapter.key_up(key)
            self.held.discard(key)
        release_each([lambda key=key: release(key) for key in tuple(self.held)])

    def release_keys(self): self._release()
    def release_all(self):
        release_each([self._release, self.adapter.release_all])


class MouseController:
    def __init__(self, adapter: InputAdapter, profile: Profile,
                 layout: MonitorLayout | None = None,
                 calibration: MouseCalibration | None = None,
                 screen: tuple[int, int] | None = None):
        self.adapter, self.profile = adapter, profile
        fallback = ScreenRegion(0, 0, *(screen or (1920, 1080)), "fallback")
        self.layout = layout or MonitorLayout([fallback], "fixed")
        self.calibration = calibration or MouseCalibration()
        self.last = None
        self.left_down = self.right_down = False
        self.middle_down = False
        self.pinch_started: dict[str, float] = {}
        self.pending_pinch = None
        self.pending_since = None
        self.pinch_latched = False
        self.pinch_ready_at = {}
        self.pinch_decision = 'idle'
        self.raw_pinches = (False, False)
        self.last_move_time = None
        self.recovering_pointer = False
        self.last_scroll_y: float | None = None
        self.paused = True
        self.status = "paused"
        self.target_region = self.layout.regions[0]
        self.edge_switcher = EdgeDwellSwitcher(
            self.layout.regions,
            float(self.profile.thresholds.get("monitor_edge_zone", .08)),
            float(self.profile.thresholds.get("monitor_edge_dwell_seconds", .8)),
        )
        from .thumb_control import ThumbControl
        self.thumb_control = ThumbControl(self)

    def update(self, hand: HandObservation | None, frame_size=(640, 480)) -> None:
        if not hand or hand.confidence < .5:
            self.release_all(); self.paused = True; self.status = "no_hand"; self.last = None; return
        if len(hand.landmarks) < 21:
            self.release_all(); self.paused = True; self.status = "invalid_hand"; return
        calibration = getattr(self, 'pose_calibration', None)
        thumb = calibration.thumb(hand, frame_size) if calibration else thumb_state(hand, frame_size)
        if (is_closed_fist(hand, frame_size) and
                (self.profile.pointer_mode not in {'thumb_lock', 'palm'} or thumb != 'open')):
            self.release_all(); self.paused = True; self.status = "paused"; self.last = None; return
        self.paused = False
        if self.profile.pointer_mode in {'thumb_lock', 'palm'}:
            self.thumb_control.update(hand, frame_size)
            return
        close = self.profile.thresholds.get("pinch_close_ratio", .35)
        open_ = self.profile.thresholds.get("pinch_open_ratio", .5)
        primary_gesture = self.profile.thresholds.get(
            "mouse_primary_click_gesture", "pinch_index")
        secondary_gesture = self.profile.thresholds.get(
            "mouse_secondary_click_gesture", "pinch_middle")
        now = time.monotonic()
        for gesture, tip in (("pinch_index", 8), ("pinch_middle", 12)):
            prepared = (finger_extended(hand, tip, frame_size) or
                        (tip == 8 and classify_mouse_pose(hand, frame_size) == 'point'))
            if (prepared and
                    not pinch(hand, 4, tip, close, open_, True)):
                self.pinch_ready_at[gesture] = now
        left = self._configured_pinch(
            hand, primary_gesture, close, open_, self.left_down)
        right = self._configured_pinch(
            hand, secondary_gesture, close, open_, self.right_down)
        pinch_present = left or right
        self.raw_pinches = (left, right)
        ambiguous = left and right and not (self.left_down or self.right_down)
        left = left and self._pinch_can_start('left', primary_gesture, now)
        right = right and self._pinch_can_start('right', secondary_gesture, now)
        if ambiguous:
            left = right = False
        # Opening means beyond the release threshold, including pending pinches.
        both_open = not any(self._configured_pinch(hand, gesture, close, open_, True)
                            for gesture in (primary_gesture, secondary_gesture))
        left, right = self._confirm_pinch(left, right, both_open, now)
        states = finger_states(hand, frame_size)
        raw_pose = classify_mouse_pose(hand, frame_size)
        scroll_gesture = self.profile.thresholds.get(
            "mouse_scroll_gesture", "peace")
        scroll_pose = raw_pose == scroll_gesture and not pinch_present
        cursor = self.adapter.position()
        self.target_region = self.layout.target(cursor)
        edge_switch_enabled = (
            self.layout.mode == "active"
            and bool(self.profile.thresholds.get("monitor_edge_switch_enabled", True))
            and len(self.layout.regions) > 1
        )
        normalized_x = ((hand.landmarks[8][0] - self.calibration.left) /
                        max(self.calibration.right - self.calibration.left, .01))
        point_pose = states == (True, False, False, False) and not pinch_present
        switched = self.edge_switcher.update(
            normalized_x, self.target_region, now,
            active=edge_switch_enabled and point_pose,
        )
        if switched is not None:
            center = (switched.x + switched.width / 2, switched.y + switched.height / 2)
            self.adapter.move(*center)
            self.target_region = switched
            self.last = center
            self.status = f"switched_{self.edge_switcher.pending_edge}"
            return

        if scroll_pose:
            self.recovering_pointer = self.last is not None
            self.last_move_time = None
            self._button("left", False, now); self._button("right", False, now)
            scroll_y = (hand.landmarks[8][1] + hand.landmarks[12][1]) / 2
            if self.last_scroll_y is not None:
                delta = scroll_y - self.last_scroll_y
                deadzone = self.profile.thresholds.get("scroll_deadzone", .015)
                if abs(delta) >= deadzone:
                    amount = int(round(-delta * self.profile.thresholds.get("scroll_sensitivity", 45.0)))
                    if amount: self.adapter.scroll(amount)
            self.last_scroll_y = scroll_y
            self.status = "scroll"
            return

        self.last_scroll_y = None
        move_gesture = self.profile.thresholds.get("mouse_move_gesture", "any")
        if self.profile.pointer_mode == "index_fingertip":
            move_gesture = "point"
        can_move = move_gesture == "any" or raw_pose == move_gesture
        # Anchor before contact only for a prepared click finger. A naturally
        # folded middle finger near the thumb must not freeze normal pointing.
        approaching = any(
            self._pinch_can_start(button, gesture, now) and
            self._configured_pinch(hand, gesture, close, open_, True)
            for button, gesture in [('left', primary_gesture), ('right', secondary_gesture)])
        early_hold = any(now - started < self.profile.thresholds.get('drag_hold_seconds', .4)
                         for started in self.pinch_started.values())
        anchor_click = (approaching and not (self.left_down or self.right_down)) or early_hold
        if anchor_click:
            can_move = False
        if raw_pose == 'curled':
            can_move = False
        if can_move:
            move_elapsed = (1 / 30 if self.last_move_time is None else
                            max(1 / 240, min(now - self.last_move_time, .05)))
            target = self.calibration.map_to_region(
                hand.landmarks[8][0], hand.landmarks[8][1], self.target_region)
            smoothing = self.profile.thresholds.get("cursor_smoothing", .6)
            if self.profile.thresholds.get("cursor_adaptive_smoothing", False):
                elapsed = (1 / 30 if self.last_move_time is None else
                           max(1 / 240, min(now - self.last_move_time, .1)))
                if self.last is not None:
                    # Small corrections are filtered; larger motion catches up quickly.
                    distance = math.dist(target, self.last)
                    blend = min(1.0, distance / 80.0)
                    response = smoothing * .5 + (1.0 - smoothing * .5) * blend
                    smoothing = 1 - (1 - response) ** (elapsed * 30)
            self.last_move_time = now
            if self.last is None:
                smoothed = target
            else:
                smoothed = (self.last[0] * (1 - smoothing) + target[0] * smoothing,
                            self.last[1] * (1 - smoothing) + target[1] * smoothing)
            if self.recovering_pointer and self.last is not None:
                limit = .12 * math.hypot(self.target_region.width, self.target_region.height) * move_elapsed * 30
                step = math.dist(smoothed, self.last)
                if step > limit:
                    smoothed = tuple(a + (b - a) * limit / step
                                     for a, b in zip(self.last, smoothed))
                else:
                    self.recovering_pointer = False
            deadzone_px = self.profile.thresholds.get("cursor_deadzone_px", .5)
            if self.profile.thresholds.get('cursor_adaptive_smoothing', False):
                # Compare against the last emitted position, so slow deliberate
                # movement accumulates and eventually leaves the resting radius.
                radius = max(1.5, .0015 * math.hypot(self.target_region.width, self.target_region.height))
                if self.last is not None and math.dist(target, self.last) <= radius:
                    smoothed = self.last
            if self.last is None or math.dist(smoothed, self.last) >= deadzone_px:
                self.adapter.move(*smoothed)
                self.last = smoothed
        else:
            self.recovering_pointer = self.last is not None
            self.last_move_time = None

        self._button("left", left, now)
        self._button("right", right, now)
        if self.left_down:
            self.status = self._pinch_status("left", now)
        elif self.right_down:
            self.status = self._pinch_status("right", now)
        else:
            self.status = "move" if can_move else f"waiting_{move_gesture}"
        if self.edge_switcher.progress > 0:
            self.status = (f"switch_{self.edge_switcher.pending_edge}_"
                           f"{int(self.edge_switcher.progress * 100)}%")

    def _button(self, button, active, now):
        attr = "left_down" if button == "left" else "right_down"
        was = getattr(self, attr)
        if active and not was:
            self.adapter.button_down(button)
            self.pinch_started[button] = now
        elif was and not active:
            self.adapter.button_up(button)
            self.pinch_started.pop(button, None)
        setattr(self, attr, active)

    def _confirm_pinch(self, left, right, both_open, now):
        if both_open:
            self.pinch_decision = 'open'
            self.pending_pinch = self.pending_since = None
            self.pinch_latched = False
            return False, False
        if self.left_down or self.right_down:
            self.pinch_decision = 'held_or_releasing'
            self.pinch_latched = True
            return left and self.left_down, right and self.right_down
        if self.pinch_latched:
            self.pinch_decision = 'wait_for_both_open'
            return False, False
        candidate = 'left' if left and not right else 'right' if right and not left else None
        if candidate is None:
            self.pinch_decision = ('ambiguous' if all(self.raw_pinches) else
                                   'extend_finger_first' if any(self.raw_pinches) else 'no_pinch')
            self.pending_pinch = self.pending_since = None
            return False, False
        if candidate != self.pending_pinch:
            self.pending_pinch, self.pending_since = candidate, now
        delay = self.profile.thresholds.get('pinch_confirm_seconds', .08)
        if now - self.pending_since + 1e-9 < delay:
            self.pinch_decision = 'confirming_' + candidate
            return False, False
        self.pinch_decision = 'activated_' + candidate
        self.pinch_latched = True
        return candidate == 'left', candidate == 'right'

    @staticmethod
    def _configured_pinch(hand, gesture, close, open_, active):
        if gesture == "pinch_index":
            return pinch(hand, 4, 8, close, open_, active)
        if gesture == "pinch_middle":
            return pinch(hand, 4, 12, close, open_, active)
        return False

    def _pinch_can_start(self, button, gesture, now):
        if getattr(self, f'{button}_down') or self.pending_pinch == button:
            return True
        ready = self.pinch_ready_at.get(gesture)
        return ready is not None and 0 <= now - ready <= .8

    def _pinch_status(self, button: str, now: float) -> str:
        elapsed = now - self.pinch_started.get(button, now)
        suffix = "drag" if elapsed >= self.profile.thresholds.get("drag_hold_seconds", .4) else "click"
        return f"{button}_{suffix}"

    @staticmethod
    def _is_fist(hand):
        return is_closed_fist(hand)

    def release_all(self):
        self.pinch_decision = 'released'
        self.thumb_control.reset()
        self.recovering_pointer = False
        self.raw_pinches = (False, False)
        self.pinch_ready_at.clear()
        self.pending_pinch = self.pending_since = None
        self.pinch_latched = False
        self.last_move_time = None
        self.last_scroll_y = None
        self.edge_switcher.reset()
        self.last = None
        def release(button):
            self.adapter.button_up(button)
            setattr(self, f"{button}_down", False)
            self.pinch_started.pop(button, None)
        release_each([lambda button=button: release(button)
                      for button in ("left", "right", "middle")
                      if getattr(self, f"{button}_down")])
