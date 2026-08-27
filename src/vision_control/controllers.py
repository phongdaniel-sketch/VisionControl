import math
import time

from .calibration import MouseCalibration
from .gestures import classify_static, finger_states, pinch
from .input_adapter import InputAdapter
from .monitors import EdgeDwellSwitcher, MonitorLayout, ScreenRegion
from .profile import Profile
from .types import HandObservation


class GestureController:
    def __init__(self, adapter: InputAdapter, profile: Profile):
        self.adapter, self.profile = adapter, profile
        self.current = "none"
        self.on_count = self.off_count = 0
        self.held: set[str] = set()

    def update(self, hand: HandObservation | None) -> str:
        if not hand or hand.confidence < self.profile.thresholds.get("gesture_confidence", .7):
            self._release(); return "none"
        gesture, _ = classify_static(hand)
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
                                self.adapter.key_down(key)
                                pressed.append(key)
                        finally:
                            for key in reversed(pressed):
                                self.adapter.key_up(key)
            else:
                for key in binding.keys:
                    if key not in self.held: self.adapter.key_down(key); self.held.add(key)
        return gesture

    def _release(self):
        for key in tuple(self.held): self.adapter.key_up(key)
        self.held.clear(); self.current = "none"; self.on_count = 0

    def release_keys(self): self._release()
    def release_all(self): self._release(); self.adapter.release_all()


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
        self.pinch_started: dict[str, float] = {}
        self.last_scroll_y: float | None = None
        self.paused = True
        self.status = "paused"
        self.target_region = self.layout.regions[0]
        self.edge_switcher = EdgeDwellSwitcher(
            self.layout.regions,
            float(self.profile.thresholds.get("monitor_edge_zone", .08)),
            float(self.profile.thresholds.get("monitor_edge_dwell_seconds", .8)),
        )

    def update(self, hand: HandObservation | None, frame_size=(640, 480)) -> None:
        if not hand or hand.confidence < .5:
            self.release_all(); self.paused = True; self.status = "no_hand"; self.last = None; return
        if len(hand.landmarks) < 21:
            self.release_all(); self.paused = True; self.status = "invalid_hand"; return
        if self._is_fist(hand):
            self.release_all(); self.paused = True; self.status = "paused"; self.last = None; return
        self.paused = False
        close = self.profile.thresholds.get("pinch_close_ratio", .35)
        open_ = self.profile.thresholds.get("pinch_open_ratio", .5)
        left = pinch(hand, 4, 8, close, open_, self.left_down)
        right = pinch(hand, 4, 12, close, open_, self.right_down)
        states = finger_states(hand)
        scroll_pose = states == (True, True, False, False) and not left and not right
        now = time.monotonic()
        cursor = self.adapter.position()
        self.target_region = self.layout.target(cursor)
        edge_switch_enabled = (
            self.layout.mode == "active"
            and bool(self.profile.thresholds.get("monitor_edge_switch_enabled", True))
            and len(self.layout.regions) > 1
        )
        normalized_x = ((hand.landmarks[8][0] - self.calibration.left) /
                        max(self.calibration.right - self.calibration.left, .01))
        point_pose = states == (True, False, False, False) and not left and not right
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
        target = self.calibration.map_to_region(hand.landmarks[8][0], hand.landmarks[8][1], self.target_region)
        smoothing = self.profile.thresholds.get("cursor_smoothing", .35)
        if self.last is None:
            smoothed = target
        else:
            smoothed = (self.last[0] * (1 - smoothing) + target[0] * smoothing,
                        self.last[1] * (1 - smoothing) + target[1] * smoothing)
        deadzone_px = self.profile.thresholds.get("cursor_deadzone_px", 2.0)
        if self.last is None or math.dist(smoothed, self.last) >= deadzone_px:
            self.adapter.move(*smoothed)
            self.last = smoothed

        self._button("left", left, now)
        self._button("right", right, now)
        if self.left_down:
            self.status = self._pinch_status("left", now)
        elif self.right_down:
            self.status = self._pinch_status("right", now)
        else:
            self.status = "move"
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

    def _pinch_status(self, button: str, now: float) -> str:
        elapsed = now - self.pinch_started.get(button, now)
        suffix = "drag" if elapsed >= self.profile.thresholds.get("drag_hold_seconds", .4) else "click"
        return f"{button}_{suffix}"

    @staticmethod
    def _is_fist(hand):
        p = hand.landmarks
        return all(p[tip][1] >= p[pip][1] for tip, pip in zip((8, 12, 16, 20), (6, 10, 14, 18)))

    def release_all(self):
        if self.left_down: self.adapter.button_up("left")
        if self.right_down: self.adapter.button_up("right")
        self.left_down = self.right_down = False
        self.pinch_started.clear()
        self.last_scroll_y = None
        self.edge_switcher.reset()
