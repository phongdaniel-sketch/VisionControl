from dataclasses import dataclass
from .gestures import classify_static, pinch
from .input_adapter import InputAdapter
from .profile import Profile
from .types import ActionIntent, HandObservation


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
                    for key in binding.keys: self.adapter.key_press(key)
            else:
                for key in binding.keys:
                    if key not in self.held: self.adapter.key_down(key); self.held.add(key)
        return gesture

    def _release(self):
        for key in tuple(self.held): self.adapter.key_up(key)
        self.held.clear(); self.current = "none"; self.on_count = 0

    def release_all(self): self._release(); self.adapter.release_all()


class MouseController:
    def __init__(self, adapter: InputAdapter, profile: Profile, screen=(1920, 1080)):
        self.adapter, self.profile, self.screen = adapter, profile, screen
        self.last = None; self.left_down = self.right_down = False; self.paused = True

    def update(self, hand: HandObservation | None, frame_size=(640, 480)) -> None:
        if not hand or hand.confidence < .5:
            self.release_all(); return
        if len(hand.landmarks) < 21: return
        index = hand.landmarks[8]
        if self._is_fist(hand):
            self.release_all(); self.paused = True; return
        self.paused = False
        x = max(0, min(self.screen[0] - 1, index[0] * self.screen[0]))
        y = max(0, min(self.screen[1] - 1, index[1] * self.screen[1]))
        if self.last is None: self.last = (x, y)
        else:
            x = self.last[0] * .65 + x * .35; y = self.last[1] * .65 + y * .35; self.last = (x, y)
        self.adapter.move(x, y)
        close = self.profile.thresholds.get("pinch_close_ratio", .35)
        open_ = self.profile.thresholds.get("pinch_open_ratio", .5)
        left = pinch(hand, 4, 8, close, open_, self.left_down)
        right = pinch(hand, 4, 12, close, open_, self.right_down)
        self._button("left", left); self._button("right", right)

    def _button(self, button, active):
        attr = "left_down" if button == "left" else "right_down"
        was = getattr(self, attr)
        if active and not was: self.adapter.button_down(button)
        elif was and not active: self.adapter.button_up(button)
        setattr(self, attr, active)

    @staticmethod
    def _is_fist(hand):
        p = hand.landmarks
        return all(p[tip][1] >= p[pip][1] for tip, pip in zip((8, 12, 16, 20), (6, 10, 14, 18)))

    def release_all(self):
        if self.left_down: self.adapter.button_up("left")
        if self.right_down: self.adapter.button_up("right")
        self.left_down = self.right_down = False
