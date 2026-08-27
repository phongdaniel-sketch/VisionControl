import argparse
import time
from pathlib import Path
from .arming import ArmingController
from .camera import Camera
from .calibration import CalibrationSession, load_calibration, save_calibration
from .controllers import GestureController, MouseController
from .input_adapter import PynputInputAdapter
from .profile import load_profile
from .tracker import MediaPipeTracker
from .overlay import Overlay
from .roles import assign_roles
from .monitors import discover_monitors
from .gestures import classify_static
from .startup import StartupCancelled, StartupScreen
from .paths import resource_root, runtime_data_dir


def run(camera_index=0, start_paused=False, profile_path=None):
    import cv2
    root = resource_root()
    adapter = mouse = keyboard = camera = tracker = None
    try:
        startup = StartupScreen(cv2, root / "docs" / "Splash Screen.png",
                                root / "docs" / "Loading Screen.png")
        startup.show_splash(1000)
        startup.show_loading(.08, "Loading profile")
        profile = load_profile(profile_path or root / "config" / "default_profile.json")
        startup.show_loading(.20, "Initializing input adapter")
        adapter = PynputInputAdapter()
        startup.show_loading(.32, "Detecting monitors")
        layout = discover_monitors(profile.monitor_mode, profile.fixed_monitor)
        calibration_path = runtime_data_dir() / "mouse_calibration.json"
        calibration = load_calibration(calibration_path)
        mouse = MouseController(adapter, profile, layout, calibration)
        keyboard = GestureController(adapter, profile)
        arming = ArmingController(profile.arming)
        startup.show_loading(.52, "Loading hand tracking model")
        tracker = MediaPipeTracker()
        startup.show_loading(.82, "Opening camera")
        camera = Camera(index=camera_index)
        camera.open()
        startup.show_loading(1.0, "Ready", 250)
        overlay = Overlay(cv2)
        calibration_session = CalibrationSession()
        paused = start_paused
        last_log = 0.0
        while True:
            frame = camera.read()
            frame = cv2.flip(frame, 1)
            result = tracker.track(frame, time.monotonic())
            mouse_hand, keyboard_hand = assign_roles(result, profile.mouse_hand,
                                                      profile.keyboard_hand,
                                                      profile.swap_hands)
            now = time.monotonic()
            raw_gesture = "none"
            if keyboard_hand is not None and keyboard_hand.confidence >= profile.thresholds.get("gesture_confidence", .7):
                raw_gesture, _ = classify_static(keyboard_hand)
            if calibration_session.active:
                mouse.release_all(); keyboard.release_keys(); arming.disarm()
                mouse.status = "calibrating"
                gesture = f"calibrate:{calibration_session.stage}"
            elif not paused:
                mouse.update(mouse_hand, (result.width, result.height))
                arming_event = arming.update(raw_gesture, keyboard_hand is not None, now)
                if arming_event in {"disarmed", "auto_disarmed"}:
                    keyboard.release_keys()
                if keyboard_hand is None:
                    keyboard.update(None)
                    gesture = "none"
                elif profile.arming.enabled and raw_gesture == profile.arming.gesture:
                    keyboard.release_keys()
                    gesture = raw_gesture
                elif arming.armed:
                    gesture = keyboard.update(keyboard_hand)
                else:
                    keyboard.release_keys()
                    gesture = raw_gesture
            else:
                arming.disarm(); keyboard.release_keys(); mouse.release_all()
                gesture = "paused"
            help_text = ""
            if calibration_session.active:
                help_text = f"Move right index to {calibration_session.stage}; SPACE=capture, R=cancel"
            overlay.draw(frame, paused=paused, mouse_role=profile.mouse_hand,
                         keyboard_role=profile.keyboard_hand, gesture=gesture,
                         hands=result.hands, mouse_found=mouse_hand is not None,
                         keyboard_found=keyboard_hand is not None,
                         mouse_status=mouse.status, monitor_name=mouse.target_region.name,
                         keyboard_state=arming.label, arming_progress=arming.progress,
                         error=help_text)
            if now - last_log >= 1.0:
                labels = [(h.label, round(h.confidence, 2)) for h in result.hands]
                print(f"[vision] camera={camera_index} swap_hands={profile.swap_hands} hands={labels} mouse_found={mouse_hand is not None} "
                      f"keyboard_found={keyboard_hand is not None} gesture={gesture} "
                      f"keyboard_state={arming.label} arming_progress={arming.progress:.2f} "
                      f"mouse_status={mouse.status} monitor={mouse.target_region.name}", flush=True)
                last_log = now
            cv2.imshow("VisionControl", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27: break
            if key in (ord("c"), ord("C")) and not calibration_session.active:
                calibration_session.start()
                mouse.release_all(); keyboard.release_keys(); arming.disarm()
            elif key == ord(" ") and calibration_session.active and mouse_hand is not None:
                point = mouse_hand.landmarks[8]
                if calibration_session.capture(point[0], point[1]):
                    try:
                        calibration = calibration_session.result()
                        save_calibration(calibration_path, calibration)
                        mouse.calibration = calibration
                    except ValueError as exc:
                        print(f"[calibration] rejected: {exc}", flush=True)
                        calibration_session.cancel()
            elif key in (ord("r"), ord("R")) and calibration_session.active:
                calibration_session.cancel()
            elif key in (ord("p"), ord("P")) and not calibration_session.active:
                paused = not paused
                if paused: mouse.release_all(); keyboard.release_keys(); arming.disarm()
    except (KeyboardInterrupt, StartupCancelled):
        pass
    except Exception as exc:
        print(f"[startup] failed: {exc}", flush=True)
        try:
            startup.show_loading(1.0, f"Failed: {exc}", 1500)
        except Exception:
            pass
        raise
    finally:
        if mouse is not None: mouse.release_all()
        if keyboard is not None: keyboard.release_all()
        if adapter is not None: adapter.release_all()
        if camera is not None: camera.close()
        if tracker is not None: tracker.close()
        cv2.destroyAllWindows()


def main(argv=None):
    parser = argparse.ArgumentParser(description="VisionControl webcam controller")
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--start-paused", action="store_true")
    parser.add_argument("--profile", type=Path)
    args = parser.parse_args(argv)
    run(args.camera_index, args.start_paused, args.profile)


if __name__ == "__main__":
    main()
