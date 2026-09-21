"""Thumb-locked curl clicks and independently prepared relative pinch drag."""
import math
import time
from .gestures import _geometry, _joint_angle, finger_extended, pinch, thumb_state
from .locked_clicks import LockedFingerClicks, ContactClick
from .cursor_filter import CursorFilter, output_step

class ThumbControl:
    def __init__(self, owner):
        self.owner = owner
        self.reset()

    def reset(self):
        self.clicks = LockedFingerClicks()
        self.right_contact = ContactClick()
        self.ready_at = self.pending_at = None
        self.release_since = None
        self.palm_anchor = self.cursor_anchor = None
        self.filter = CursorFilter()
        self.predict_enabled = False
        self.last_emit_time = None

    @staticmethod
    def finger(hand, tip, size, calibration=None):
        if calibration is not None:
            return calibration.finger(hand, tip, size)
        if finger_extended(hand, tip, size): return 'extended'
        points = _geometry(hand, size)
        if points is None: return 'unknown'
        angle = _joint_angle(points[tip-3], points[tip-2], points[tip])
        return 'curled' if angle is not None and angle <= 110 else 'unknown'

    def move(self, target, predict=False):
        o = self.owner
        if predict:
            if not self.predict_enabled:self.filter.reset()
            self.predict_enabled = True
            target = self.filter.update(target,getattr(o,'sample_time',time.monotonic()),
                                        math.hypot(o.target_region.width,o.target_region.height))
            predicted = self.filter.predict(time.monotonic(),
                                            math.hypot(o.target_region.width,o.target_region.height))
            if predicted is not None:
                target = predicted
        else:
            self.predict_enabled = False
        self.emit(target)

    def emit(self, target):
        o = self.owner
        r = o.target_region
        target = (max(r.x,min(r.x+r.width-1,target[0])),max(r.y,min(r.y+r.height-1,target[1])))
        current = o.adapter.position()
        now = time.monotonic()
        elapsed = 1 / 60 if self.last_emit_time is None else now - self.last_emit_time
        self.last_emit_time = now
        d = math.dist(current, target)
        diagonal = math.hypot(o.target_region.width, o.target_region.height)
        if d <= max(1.5, diagonal*.0015): return
        step = output_step(d, diagonal, elapsed)
        if step <= 0:
            return
        o.adapter.move(*(a+(b-a)*step/d for a,b in zip(current,target)))
        o.last = o.adapter.position()

    def advance(self, now):
        if not self.predict_enabled or self.owner.status not in {'move', 'left_click', 'right_click', 'middle_click'}:return
        r = self.owner.target_region
        target = self.filter.predict(now,math.hypot(r.width,r.height))
        if target is not None:self.emit(target)

    def update(self, hand, size):
        o = self.owner
        now = time.monotonic()
        palm_mode = o.profile.pointer_mode == 'palm'
        if _geometry(hand, size) is None:
            o.release_all(); o.status = 'invalid_hand'; return
        calibration = getattr(o, 'pose_calibration', None)
        thumb = calibration.thumb(hand, size) if calibration else thumb_state(hand, size)
        o.target_region = o.layout.target(o.adapter.position())
        close = o.profile.thresholds.get('pinch_close_ratio', .28)
        opened = o.profile.thresholds.get('pinch_open_ratio', .45)
        touching = pinch(hand,4,8,close,opened,o.left_down or self.pending_at is not None)
        separated = not pinch(hand,4,8,close,opened,True)
        middle_touching = pinch(hand,4,12,close,opened,False)
        middle_separated = not pinch(hand,4,12,close,opened,True)
        if separated and middle_separated and not o.left_down:
            self.ready_at = now
        palm = tuple(sum(hand.landmarks[i][axis] for i in (0,5,9,13,17))/5 for axis in (0,1))
        o.raw_pinches = (touching,middle_touching)
        if o.left_down:
            self.right_contact.reset()
            self.predict_enabled = False
            self.clicks.clear_cycle()
            if not touching:
                if self.release_since is None:
                    self.release_since = now
                if now-self.release_since+1e-9 < o.profile.thresholds.get('pinch_release_seconds', .1):
                    o.pinch_decision = 'confirming_release'; o.status = 'drag_release_pending'
                    return
                o._button('left',False,now)
                self.pending_at = self.ready_at = None
                self.release_since = None
                self.palm_anchor = self.cursor_anchor = None
                o.pinch_decision = 'drag_released'; o.status = 'drag_released'
                return
            self.release_since = None
            dx = (palm[0]-self.palm_anchor[0]) / (o.calibration.right-o.calibration.left)
            dy = (palm[1]-self.palm_anchor[1]) / (o.calibration.bottom-o.calibration.top)
            region = o.target_region
            target = (max(region.x,min(region.x+region.width-1,self.cursor_anchor[0]+dx*region.width)),
                      max(region.y,min(region.y+region.height-1,self.cursor_anchor[1]+dy*region.height)))
            self.move(target)
            o.status = 'left_drag'; o.pinch_decision = 'drag_held'; return
        right_click = self.right_contact.update(
            middle_touching, separated and middle_separated,
            conflict=touching and not middle_separated)
        if not middle_separated or self.right_contact.latched:
            self.predict_enabled = False
            self.clicks.clear_cycle()
            self.pending_at = self.ready_at = None
            o.pinch_decision = 'right_contact' if not touching else 'ambiguous_pinch'
            o.status = 'right_contact' if not touching else 'separate_fingertips_first'
            if right_click:
                try:
                    o.right_down = True
                    o.adapter.button_down('right')
                finally:
                    o.adapter.button_up('right')
                    o.right_down = False
                o.status = 'right_click'
            return
        if touching:
            self.predict_enabled = False
            self.clicks.clear_cycle()
            if self.pending_at is None and self.ready_at is not None:
                self.pending_at = now
            o.pinch_decision = 'confirming_drag' if self.pending_at is not None else 'separate_fingertips_first'
            o.status = 'confirming_drag' if self.pending_at is not None else 'separate_thumb_and_index'
            if self.pending_at is not None and now-self.pending_at+1e-9 >= o.profile.thresholds.get('pinch_confirm_seconds', .1):
                self.cursor_anchor = o.adapter.position()
                self.palm_anchor = palm
                o.left_down = True
                o.adapter.button_down('left')
                o.pinch_started['left'] = now
                o.status = 'left_drag'; o.pinch_decision = 'drag_started'
            return
        self.pending_at = None
        fingers = {name:self.finger(hand,tip,size,calibration) for name,tip in [('index',8),('middle',12)]}
        buttons = self.clicks.update(thumb,fingers,False,now)
        o.pinch_decision = 'open'
        if not palm_mode and (thumb != 'tucked' or self.clicks.locked):
            self.predict_enabled = False
            o.status = 'locked' if self.clicks.locked else 'locking'
            for button in buttons:
                try:
                    setattr(o,button+'_down',True)
                    o.adapter.button_down(button)
                finally:
                    o.adapter.button_up(button)
                    setattr(o,button+'_down',False)
                o.status = button+'_click'
            return
        source = palm if palm_mode else hand.landmarks[8]
        target = o.calibration.map_to_region(source[0],source[1],o.target_region)
        self.move(target, predict=True)
        o.status = 'move'
        if palm_mode:
            for button in buttons:
                try:
                    setattr(o, button + '_down', True)
                    o.adapter.button_down(button)
                finally:
                    o.adapter.button_up(button)
                    setattr(o, button + '_down', False)
                o.status = button + '_click'
