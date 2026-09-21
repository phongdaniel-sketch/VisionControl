"""Local, bounded calibration of mouse-hand curl and thumb thresholds."""
import json
import math
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from .gestures import _geometry, _joint_angle, pinch
from .locked_clicks import LockedFingerClicks, ContactClick
from .types import distance


STAGES = ('open', 'tucked', 'index', 'middle', 'both')


def measure(hand, size):
    if hand is None or not math.isfinite(hand.confidence) or hand.confidence < .7:
        return None
    p = _geometry(hand, size)
    if p is None or any(not (0 <= x <= 1 and 0 <= y <= 1)
                        for x, y, _ in hand.landmarks):
        return None
    scale = distance(p[0], p[9])
    if scale < .025 or any(distance(p[a], p[b]) > 2.5 * scale
                           for a, b in ((5, 8), (9, 12), (13, 16), (17, 20), (0, 4))):
        return None
    angles = [_joint_angle(p[t-3], p[t-2], p[t]) for t in (8, 12)]
    thumb_angle = _joint_angle(p[2], p[3], p[4])
    axis = tuple(p[5][i] - p[17][i] for i in range(3))
    width = sum(v*v for v in axis)
    if width < 1e-8 or thumb_angle is None or any(a is None for a in angles):
        return None
    outward = sum((p[4][i]-p[5][i])*axis[i] for i in range(3)) / width
    return (*angles, outward, thumb_angle)


@dataclass(frozen=True)
class PoseCalibration:
    index_curled: float
    index_extended: float
    middle_curled: float
    middle_extended: float
    thumb_tucked: float
    thumb_open: float
    thumb_angle: float

    def validate(self):
        if any(type(v) not in (float, int) or not math.isfinite(v)
               for v in asdict(self).values()):
            raise ValueError('Non-finite pose thresholds')
        for name in ('index', 'middle'):
            curled, extended = getattr(self, name+'_curled'), getattr(self, name+'_extended')
            if not (30 <= curled <= 130 and 120 <= extended <= 170 and extended-curled >= 15):
                raise ValueError('Unsafe finger thresholds')
        if not (-.3 <= self.thumb_tucked <= .3 and .1 <= self.thumb_open <= .8
                and self.thumb_open-self.thumb_tucked >= .08 and 110 <= self.thumb_angle <= 160):
            raise ValueError('Unsafe thumb thresholds')
        return self

    def finger(self, hand, tip, size):
        values = measure(hand, size)
        if values is None or tip not in (8, 12):
            return 'unknown'
        name, angle = ('index', values[0]) if tip == 8 else ('middle', values[1])
        if angle <= getattr(self, name+'_curled'):
            return 'curled'
        if angle >= getattr(self, name+'_extended'):
            p = _geometry(hand, size)
            if distance(p[tip], p[0]) > distance(p[tip-2], p[0]) + .1*distance(p[0], p[9]):
                return 'extended'
        return 'unknown'

    def thumb(self, hand, size):
        values = measure(hand, size)
        if values is None:
            return 'unknown'
        if values[2] >= self.thumb_open and values[3] >= self.thumb_angle:
            return 'open'
        return 'tucked' if values[2] <= self.thumb_tucked else 'unknown'


def _quantile(values, fraction):
    values = sorted(values)
    return values[round((len(values)-1)*fraction)]


def fit(samples):
    if set(samples) != set(STAGES) or any(len(samples[s]) < 20 for s in STAGES):
        raise ValueError('Capture every pose before testing.')
    result = {}
    for column, name in enumerate(('index', 'middle')):
        curled_stages = (name, 'both')
        extended = [v[column] for s in STAGES if s not in curled_stages for v in samples[s]]
        curled = [v[column] for s in curled_stages for v in samples[s]]
        lo, hi = _quantile(curled, .9), _quantile(extended, .1)
        if hi-lo < 30 or hi < 130 or lo > 120:
            raise ValueError(f'{name.title()} poses overlap. Restart and make the curl more distinct.')
        result[name+'_curled'] = max(30., min(130., lo+(hi-lo)/3))
        result[name+'_extended'] = max(120., min(170., hi-(hi-lo)/3))
    tucked = _quantile([v[2] for v in samples['tucked']], .9)
    opened = _quantile([v[2] for s in STAGES if s != 'tucked' for v in samples[s]], .1)
    if opened-tucked < .24:
        raise ValueError('Thumb poses overlap. Keep the thumb open during curl samples.')
    result['thumb_tucked'] = max(-.3, min(.3, tucked+(opened-tucked)/3))
    result['thumb_open'] = max(.1, min(.8, opened-(opened-tucked)/3))
    result['thumb_angle'] = max(110., min(160., _quantile(
        [v[3] for s in STAGES if s != 'tucked' for v in samples[s]], .1)-10))
    candidate = PoseCalibration(**result).validate()
    # Clamping must not turn the captured poses into unrecognizable thresholds.
    for s in STAGES:
        for v in samples[s]:
            if (s == 'tucked' and v[2] > candidate.thumb_tucked or
                    s != 'tucked' and (v[2] < candidate.thumb_open or v[3] < candidate.thumb_angle)):
                raise ValueError('Thumb samples are inconsistent. Restart with a steady hand.')
    return candidate


class PoseCapture:
    """One explicit, continuous fresh-frame capture at a time."""
    def __init__(self):
        self.samples = {}
        self.pending = []
        self.deadline = None
        self.last_time = None
        self.first_time = None
        self.message = ''

    @property
    def stage(self):
        return STAGES[len(self.samples)] if len(self.samples) < len(STAGES) else None

    def begin(self, now):
        self.pending = []
        self.last_time = self.first_time = None
        self.deadline = now + 3.
        self.message = ''

    def reject(self, message):
        self.pending = []
        self.deadline = None
        self.message = message

    def observe(self, hand, size, stamp, now):
        if self.deadline is None or self.stage is None:
            return False
        # The countdown lets the user leave the physical mouse and form the pose.
        if now < self.deadline:
            return False
        if not math.isfinite(stamp) or now-stamp > .15 or stamp > now:
            self.reject('Tracking is stale. Retry capture.'); return False
        if self.last_time is not None and stamp <= self.last_time:
            return False
        values = measure(hand, size)
        if values is None:
            self.reject('Hand unclear or outside the preview. Retry capture.'); return False
        if self.last_time is not None and stamp-self.last_time > .15:
            self.reject('Tracking interrupted. Retry capture.'); return False
        self.last_time = stamp
        if stamp < self.deadline:
            return False
        if self.first_time is None:
            self.first_time = stamp
        self.pending.append(values)
        if stamp-self.first_time < 1.2 or len(self.pending) < 20:
            return False
        for col, limit in enumerate((20., 20., .2, 25.)):
            values = [v[col] for v in self.pending]
            if _quantile(values, .9)-_quantile(values, .1) > limit:
                self.reject('Pose moved too much. Hold steady and retry.'); return False
        self.samples[self.stage] = list(self.pending)
        self.deadline = None
        self.message = 'Sample captured.'
        return True


class PosePreview:
    """Inert click rehearsal: never imports or calls an OS input adapter."""
    def __init__(self, candidate, thresholds):
        self.candidate = candidate
        self.thresholds = thresholds
        self.clicks = LockedFingerClicks()
        self.right_contact = ContactClick()
        self.seen = set()
        self.tucked = False
        self.last_time = None
        self.label = 'Show your mouse hand.'

    @property
    def complete(self):
        return self.tucked and self.seen == {'left', 'middle', 'right'}

    def update(self, hand, size, stamp, now):
        if measure(hand, size) is None or not math.isfinite(stamp) or not 0 <= now-stamp <= .15:
            self.clicks.reset(); self.last_time = None
            self.right_contact.reset()
            self.label = 'Tracking unclear; click cycle reset.'
            return ()
        if self.last_time is not None:
            if stamp <= self.last_time:
                return ()
            if stamp-self.last_time > .15:
                self.clicks.reset()
                self.right_contact.reset()
        self.last_time = stamp
        thumb = self.candidate.thumb(hand, size)
        fingers = {n:self.candidate.finger(hand, t, size) for n,t in (('index',8),('middle',12))}
        close = self.thresholds.get('pinch_close_ratio', .28)
        opened = self.thresholds.get('pinch_open_ratio', .45)
        touching = pinch(hand, 4, 8, close, opened, False)
        middle_touching = pinch(hand, 4, 12, close, opened, False)
        middle_separated = not pinch(hand, 4, 12, close, opened, True)
        index_separated = not pinch(hand, 4, 8, close, opened, True)
        right_click = self.right_contact.update(middle_touching,
            index_separated and middle_separated, conflict=touching and not middle_separated)
        if not middle_separated or self.right_contact.latched:
            self.clicks.clear_cycle()
            buttons = ('right',) if right_click else ()
        else:
            buttons = self.clicks.update(thumb, fingers, touching, stamp)
        self.seen.update(buttons)
        self.tucked |= (thumb == 'tucked' and index_separated and middle_separated
                        and all(state == 'extended' for state in fingers.values()))
        self.label = f'Thumb: {thumb} | Index: {fingers["index"]} | Middle: {fingers["middle"]}'
        return buttons


def calibration_path(directory, profile):
    role = profile.mouse_hand.lower()
    if role not in ('left', 'right'):
        raise ValueError('Invalid mouse hand')
    return Path(directory) / f'pose_calibration_{role}_swap{int(bool(profile.swap_hands))}.json'


def load_pose_calibration(path):
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        if data['version'] != 1:
            return None
        return PoseCalibration(**data['thresholds']).validate()
    except (OSError, ValueError, TypeError, KeyError):
        return None


def save_pose_calibration(path, calibration):
    calibration.validate()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    try:
        temporary.write_text(json.dumps({'version':1, 'thresholds':asdict(calibration)}, indent=2)+'\n', encoding='utf-8')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
