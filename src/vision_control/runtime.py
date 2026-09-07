import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .arming import ArmingController
from .calibration import CalibrationSession, load_calibration, save_calibration, pointer_point, calibration_filename
from .camera import Camera
from .controllers import GestureController, MouseController
from .gestures import classify_static, classify_mouse_pose
from .input_adapter import PynputInputAdapter
from .monitors import discover_monitors
from .overlay import Overlay
from .paths import resource_root, runtime_data_dir
from .profile import load_profile
from .roles import assign_roles
from .tracker import MediaPipeTracker
from .types import HandsFrame


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
    mouse_pose: str = "none"
    keyboard_pose: str = "none"
    sample_time: float = 0.0
    timings_ms: dict = field(default_factory=dict)


class VisionRuntime:
    """Owns camera tracking and input side effects for one controller session."""

    def __init__(self, camera_index=1, start_paused=False, profile_path=None,
                 camera_factory=Camera, tracker_factory=MediaPipeTracker,
                 adapter_factory=PynputInputAdapter, async_mode=False):
        self.async_mode = async_mode
        self.perception = None
        self.accept_after = 0.
        self.debug_enabled = False
        self.landmarks_enabled = True
        self.camera_index = camera_index
        self.profile_path = Path(profile_path) if profile_path else None
        self.paused = bool(start_paused)
        self.camera_factory = camera_factory
        self.tracker_factory = tracker_factory
        self.adapter_factory = adapter_factory
        self.adapter = self.mouse = self.keyboard = None
        self.camera = self.tracker = self.overlay = None
        self.arming = None
        self.primary_v1 = self.second_v1 = None
        self.profile = None
        self.calibration_session = CalibrationSession()
        self.calibration_needed = False
        self.last_snapshot = None
        self.last_log = 0.0
        self.started = False

    def start(self, progress: Callable[[float, str], None] | None = None):
        if self.perception is not None:
            self.perception.close()
            self.perception = None
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
            calibration_path = runtime_data_dir() / calibration_filename(self.profile.pointer_mode)
            self.calibration_needed = self.profile.pointer_mode == 'palm' and not calibration_path.exists()
            calibration = load_calibration(calibration_path)
            self.mouse = MouseController(self.adapter, self.profile, layout, calibration)
            self.keyboard = GestureController(self.adapter, self.profile)
            self.arming = ArmingController(self.profile.arming)
            self.primary_v1 = self.second_v1 = None
            if self.profile.gesture_v1.get('enabled'):
                from .gesture_v1 import PrimaryHand, SecondHand
                self.primary_v1 = PrimaryHand(self.adapter, self.profile.gesture_v1)
                self.second_v1 = SecondHand(self.adapter, self.profile.gesture_v1)
            progress(.52, "Loading hand tracking model")
            if self.async_mode:
                from .perception_worker import LatestPerception
                self.perception = LatestPerception(self.camera_factory,self.tracker_factory,self.camera_index)
                self.perception.start()
            else:
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

    def suspend_perception(self):
        """Release input before relinquishing camera/model ownership."""
        self.set_paused(True)
        if self.perception is not None:
            self.perception.close()
            self.perception = None
        if self.camera is not None:
            self.camera.close()
            self.camera = None
        if self.tracker is not None:
            self.tracker.close()
            self.tracker = None
        self.last_snapshot = None

    def wake_perception(self):
        """Resume preview without reloading profiles or enabling input."""
        self.set_paused(True)
        self.last_snapshot = None
        try:
            if self.async_mode:
                from .perception_worker import LatestPerception
                self.perception = LatestPerception(
                    self.camera_factory, self.tracker_factory, self.camera_index)
                self.perception.start()
            else:
                self.tracker = self.tracker_factory()
                self.camera = self.camera_factory(index=self.camera_index)
                self.camera.open()
        except Exception:
            self.suspend_perception()
            raise

    def process_frame(self, *, status_overlay=False) -> RuntimeSnapshot:
        if not self.started:
            raise RuntimeError("VisionRuntime has not been started")
        import cv2
        before_read = time.perf_counter()
        if self.perception is not None:
            packet = self.perception.take()
            if packet is None:
                if self.last_snapshot is None or time.monotonic()-self.last_snapshot.sample_time>.15:
                    self._release_controls()
                return None
            _,frame,result,sample_time,read_ms,track_ms = packet
            if time.monotonic()-sample_time>.15 or sample_time<self.accept_after:
                self._release_controls()
                return None
            after_read = before_read
        else:
            frame = cv2.flip(self.camera.read(), 1)
            after_read = time.perf_counter()
            sample_time = time.monotonic()
            result = self.tracker.track(frame, sample_time)
            read_ms = (after_read-before_read)*1000
            track_ms = (time.perf_counter()-after_read)*1000
        after_tracking = time.perf_counter()
        mouse_hand, keyboard_hand = assign_roles(
            result, self.profile.mouse_hand, self.profile.keyboard_hand,
            self.profile.swap_hands)
        now = time.monotonic()
        raw_gesture = "none"
        confidence = self.profile.thresholds.get("gesture_confidence", .7)
        if keyboard_hand is not None and keyboard_hand.confidence >= confidence:
            raw_gesture, _ = classify_static(keyboard_hand, (result.width, result.height))
        mouse_pose = "none"
        if mouse_hand is not None and mouse_hand.confidence >= .5:
            mouse_pose = classify_mouse_pose(mouse_hand, (result.width, result.height))

        if self.calibration_session.active:
            self._release_controls()
            self.mouse.status = "calibrating"
            gesture = f"calibrate:{self.calibration_session.stage}"
        elif not self.paused and self.primary_v1 is not None:
            from .gesture_v1 import features
            if self.last_snapshot is not None and sample_time - self.last_snapshot.sample_time > .15:
                self._release_controls()
            size = (result.width, result.height)
            primary = features(mouse_hand, size, self.profile.gesture_v1)
            secondary = features(keyboard_hand, size, self.profile.gesture_v1)
            self.mouse.sample_time = sample_time
            consumed = self.primary_v1.update(primary, sample_time, self.mouse)
            if consumed:
                self.mouse.status = self.primary_v1.status
            else:
                self.mouse.update(mouse_hand, size)
            self.second_v1.update(secondary, sample_time, self.primary_v1.two_hands)
            gesture = self.second_v1.status
        elif not self.paused:
            self.mouse.sample_time = sample_time
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
                gesture = self.keyboard.update(keyboard_hand, (result.width, result.height))
            else:
                self.keyboard.release_keys()
                gesture = raw_gesture
        else:
            self._release_controls()
            gesture = "paused"

        help_text = 'Palm calibration not saved. Press Calibrate to set your movement area.' if self.calibration_needed else ''
        if self.calibration_session.active:
            source_name = 'palm center' if self.profile.pointer_mode == 'palm' else 'index fingertip'
            help_text = (f"Move {self.profile.mouse_hand.lower()} {source_name} to "
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
            keyboard_state=self.second_v1.status if self.second_v1 else self.arming.label,
            arming_progress=max(self.second_v1.progress, self.primary_v1.progress) if self.second_v1 else self.arming.progress,
            help_text=help_text,
            mouse_pose=mouse_pose,
            keyboard_pose=raw_gesture,
            sample_time=sample_time,
            timings_ms={
                'camera_read': read_ms,
                'tracking': track_ms,
                'controller': (time.perf_counter() - after_tracking) * 1000,
            },
        )
        self.last_snapshot = snapshot
        preview_enabled = getattr(self, "preview_enabled", True)
        if preview_enabled and status_overlay:
            self.overlay.draw(frame, **self._overlay_values(snapshot))
        elif preview_enabled and self.landmarks_enabled:
            self.overlay.draw_landmarks(frame, snapshot.hands)
        if preview_enabled and self.landmarks_enabled and self.profile.pointer_mode in {"index_fingertip", "thumb_lock", "palm"} and mouse_hand is not None:
            self.overlay.draw_fingertip(frame, mouse_hand)
            if self.profile.pointer_mode == 'palm':
                x, y, _ = pointer_point(mouse_hand, 'palm')
                cv2.circle(frame, (round(x * result.width), round(y * result.height)),
                           9, (220, 80, 240), 2, cv2.LINE_AA)
        snapshot.timings_ms['runtime_total'] = (time.perf_counter() - before_read) * 1000
        if self.perception is not None:
            snapshot.timings_ms['result_age'] = (time.monotonic()-sample_time)*1000
            snapshot.timings_ms['runtime_total'] += read_ms+track_ms
        if preview_enabled and self.debug_enabled and now - self.last_log >= 1.0:
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
        self.accept_after = time.monotonic()
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
        self.set_paused(True)

    def capture_calibration(self) -> bool:
        if not self.calibration_session.active or self.last_snapshot is None:
            return False
        mouse_hand, _ = assign_roles(
            HandsFrame(0, self.last_snapshot.hands), self.profile.mouse_hand,
            self.profile.keyboard_hand, self.profile.swap_hands)
        if (mouse_hand is None or len(mouse_hand.landmarks) < 21 or
                mouse_hand.confidence < .5):
            return False
        point = pointer_point(mouse_hand, self.profile.pointer_mode)
        stage = self.calibration_session.stage
        values = self.calibration_session.values
        if not (0 <= point[0] <= 1 and 0 <= point[1] <= 1):
            raise ValueError("Keep the selected pointer point inside the camera preview.")
        if stage == "right" and point[0] <= values["left"] + .05:
            raise ValueError("Move farther RIGHT in the preview, away from the saved left edge.")
        if stage == "bottom" and point[1] <= values["top"] + .05:
            raise ValueError("Move farther DOWN in the preview, away from the saved top edge.")
        complete = self.calibration_session.capture(point[0], point[1])
        if complete:
            calibration = self.calibration_session.result()
            try:
                save_calibration(runtime_data_dir() / calibration_filename(self.profile.pointer_mode), calibration)
            except Exception:
                self.calibration_session.index = 3
                self.calibration_session.active = True
                raise
            self.mouse.calibration = calibration
            self.calibration_needed = False
        return complete

    def cancel_calibration(self) -> None:
        self.calibration_session.cancel()
        self.set_paused(True)

    def close(self) -> None:
        self._release_controls()
        if self.perception is not None:
            self.perception.close()
            self.perception = None
        adapter, self.adapter = self.adapter, None
        camera, self.camera = self.camera, None
        tracker, self.tracker = self.tracker, None
        if not self._safe_cleanup("input adapter", adapter, "release_all"):
            self.adapter = adapter
        self._safe_cleanup("camera", camera, "close")
        self._safe_cleanup("hand tracker", tracker, "close")
        self.started = False

    def cursor_tick(self):
        if self.paused or self.calibration_session.active or not self.mouse:
            return
        if self.last_snapshot is None or time.monotonic()-self.last_snapshot.sample_time>.15:
            self._release_controls()
            return
        self.mouse.thumb_control.advance(time.monotonic())

    def _release_controls(self) -> None:
        self._safe_cleanup('second hand', self.second_v1, 'reset')
        self._safe_cleanup('primary gestures', self.primary_v1, 'reset')
        self._safe_cleanup("arming state", self.arming, "disarm")
        self._safe_cleanup("keyboard", self.keyboard, "release_all")
        self._safe_cleanup("mouse", self.mouse, "release_all")

    @staticmethod
    def _safe_cleanup(label, target, method) -> bool:
        if target is None:
            return True
        try:
            getattr(target, method)()
            return True
        except Exception as exc:
            print(f"[shutdown] unable to close {label}: {exc}", flush=True)
            return False

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
