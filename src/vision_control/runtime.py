import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .arming import ArmingController
from .calibration import CalibrationSession, load_calibration, save_calibration
from .camera import Camera
from .controllers import GestureController, MouseController
from .gestures import classify_static
from .input_adapter import PynputInputAdapter
from .monitors import discover_monitors
from .overlay import Overlay
from .paths import resource_root, runtime_data_dir
from .profile import load_profile
from .roles import assign_roles
from .tracker import MediaPipeTracker


@dataclass(frozen=True)
class RuntimeSnapshot:
    frame: object
    paused: bool
    mouse_role: str
    keyboard_role: str
    gesture: str
    hands: tuple
    mouse_found: bool
    keyboard_found: bool
    mouse_status: str
    monitor_name: str
    keyboard_state: str
    arming_progress: float
    help_text: str = ""


class VisionRuntime:
    """Owns camera tracking and input side effects for one controller session."""

    def __init__(self, camera_index=0, start_paused=False, profile_path=None,
                 camera_factory=Camera, tracker_factory=MediaPipeTracker,
                 adapter_factory=PynputInputAdapter):
        self.camera_index = camera_index
        self.profile_path = Path(profile_path) if profile_path else None
        self.paused = bool(start_paused)
        self.camera_factory = camera_factory
        self.tracker_factory = tracker_factory
        self.adapter_factory = adapter_factory
        self.adapter = self.mouse = self.keyboard = None
        self.camera = self.tracker = self.overlay = None
        self.arming = None
        self.profile = None
        self.calibration_session = CalibrationSession()
        self.last_snapshot = None
        self.last_log = 0.0
        self.started = False

    def start(self, progress: Callable[[float, str], None] | None = None):
        progress = progress or (lambda _value, _message: None)
        root = resource_root()
        try:
            progress(.08, "Loading profile")
            self.profile = load_profile(
                self.profile_path or root / "config" / "default_profile.json")
            progress(.20, "Initializing input adapter")
            self.adapter = self.adapter_factory()
            progress(.32, "Detecting monitors")
            layout = discover_monitors(self.profile.monitor_mode,
                                       self.profile.fixed_monitor)
            calibration_path = runtime_data_dir() / "mouse_calibration.json"
            calibration = load_calibration(calibration_path)
            self.mouse = MouseController(self.adapter, self.profile, layout, calibration)
            self.keyboard = GestureController(self.adapter, self.profile)
            self.arming = ArmingController(self.profile.arming)
            progress(.52, "Loading hand tracking model")
            self.tracker = self.tracker_factory()
            progress(.82, "Opening camera")
            self.camera = self.camera_factory(index=self.camera_index)
            self.camera.open()
            import cv2
            self.overlay = Overlay(cv2)
            self.started = True
            progress(1.0, "Ready")
            if self.paused:
                self._release_controls()
            return self
        except Exception:
            self.close()
            raise

    def process_frame(self, *, status_overlay=False) -> RuntimeSnapshot:
        if not self.started:
            raise RuntimeError("VisionRuntime has not been started")
        import cv2
        frame = cv2.flip(self.camera.read(), 1)
        result = self.tracker.track(frame, time.monotonic())
        mouse_hand, keyboard_hand = assign_roles(
            result, self.profile.mouse_hand, self.profile.keyboard_hand,
            self.profile.swap_hands)
        now = time.monotonic()
        raw_gesture = "none"
        confidence = self.profile.thresholds.get("gesture_confidence", .7)
        if keyboard_hand is not None and keyboard_hand.confidence >= confidence:
            raw_gesture, _ = classify_static(keyboard_hand)

        if self.calibration_session.active:
            self._release_controls()
            self.mouse.status = "calibrating"
            gesture = f"calibrate:{self.calibration_session.stage}"
        elif not self.paused:
            self.mouse.update(mouse_hand, (result.width, result.height))
            arming_event = self.arming.update(
                raw_gesture, keyboard_hand is not None, now)
            if arming_event in {"disarmed", "auto_disarmed"}:
                self.keyboard.release_keys()
            if keyboard_hand is None:
                self.keyboard.update(None)
                gesture = "none"
            elif (self.profile.arming.enabled and
                  raw_gesture == self.profile.arming.gesture):
                self.keyboard.release_keys()
                gesture = raw_gesture
            elif self.arming.armed:
                gesture = self.keyboard.update(keyboard_hand)
            else:
                self.keyboard.release_keys()
                gesture = raw_gesture
        else:
            self._release_controls()
            gesture = "paused"

        help_text = ""
        if self.calibration_session.active:
            help_text = (f"Move {self.profile.mouse_hand.lower()} index to "
                         f"{self.calibration_session.stage}; SPACE=capture, R=cancel")
        snapshot = RuntimeSnapshot(
            frame=frame,
            paused=self.paused,
            mouse_role=self.profile.mouse_hand,
            keyboard_role=self.profile.keyboard_hand,
            gesture=gesture,
            hands=tuple(result.hands),
            mouse_found=mouse_hand is not None,
            keyboard_found=keyboard_hand is not None,
            mouse_status=self.mouse.status,
            monitor_name=self.mouse.target_region.name,
            keyboard_state=self.arming.label,
            arming_progress=self.arming.progress,
            help_text=help_text,
        )
        self.last_snapshot = snapshot
        if status_overlay:
            self.overlay.draw(frame, **self._overlay_values(snapshot))
        else:
            self.overlay.draw_landmarks(frame, snapshot.hands)
        if now - self.last_log >= 1.0:
            labels = [(hand.label, round(hand.confidence, 2))
                      for hand in snapshot.hands]
            print(
                f"[vision] camera={self.camera_index} "
                f"swap_hands={self.profile.swap_hands} hands={labels} "
                f"mouse_found={snapshot.mouse_found} "
                f"keyboard_found={snapshot.keyboard_found} "
                f"gesture={snapshot.gesture} "
                f"keyboard_state={snapshot.keyboard_state} "
                f"arming_progress={snapshot.arming_progress:.2f} "
                f"mouse_status={snapshot.mouse_status} "
                f"monitor={snapshot.monitor_name}", flush=True)
            self.last_log = now
        return snapshot

    def set_paused(self, paused: bool) -> None:
        self.paused = bool(paused)
        if self.paused:
            self._release_controls()

    def toggle_paused(self) -> bool:
        if self.calibration_session.active:
            return self.paused
        self.set_paused(not self.paused)
        return self.paused

    def start_calibration(self) -> None:
        if self.calibration_session.active:
            return
        self.calibration_session.start()
        self._release_controls()

    def capture_calibration(self) -> bool:
        if not self.calibration_session.active or self.last_snapshot is None:
            return False
        mouse_hand = next(
            (hand for hand in self.last_snapshot.hands
             if hand.label == self.profile.mouse_hand), None)
        if self.profile.swap_hands:
            expected = "Left" if self.profile.mouse_hand == "Right" else "Right"
            mouse_hand = next(
                (hand for hand in self.last_snapshot.hands if hand.label == expected),
                mouse_hand)
        if mouse_hand is None:
            return False
        point = mouse_hand.landmarks[8]
        complete = self.calibration_session.capture(point[0], point[1])
        if complete:
            calibration = self.calibration_session.result()
            save_calibration(runtime_data_dir() / "mouse_calibration.json", calibration)
            self.mouse.calibration = calibration
        return complete

    def cancel_calibration(self) -> None:
        self.calibration_session.cancel()

    def close(self) -> None:
        self._release_controls()
        if self.adapter is not None:
            self.adapter.release_all()
        if self.camera is not None:
            self.camera.close()
        if self.tracker is not None:
            self.tracker.close()
        self.started = False

    def _release_controls(self) -> None:
        if self.arming is not None:
            self.arming.disarm()
        if self.keyboard is not None:
            self.keyboard.release_all()
        if self.mouse is not None:
            self.mouse.release_all()

    @staticmethod
    def _overlay_values(snapshot: RuntimeSnapshot) -> dict:
        return {
            "paused": snapshot.paused,
            "mouse_role": snapshot.mouse_role,
            "keyboard_role": snapshot.keyboard_role,
            "gesture": snapshot.gesture,
            "hands": snapshot.hands,
            "mouse_found": snapshot.mouse_found,
            "keyboard_found": snapshot.keyboard_found,
            "mouse_status": snapshot.mouse_status,
            "monitor_name": snapshot.monitor_name,
            "keyboard_state": snapshot.keyboard_state,
            "arming_progress": snapshot.arming_progress,
            "error": snapshot.help_text,
        }
