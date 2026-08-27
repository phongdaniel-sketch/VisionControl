import argparse
import time
from pathlib import Path
from .camera import Camera
from .calibration import CalibrationSession, load_calibration, save_calibration
from .controllers import GestureController, MouseController
from .input_adapter import PynputInputAdapter
from .profile import load_profile
from .tracker import MediaPipeTracker
from .overlay import Overlay
from .roles import assign_roles
from .monitors import discover_monitors


def run(camera_index=0, start_paused=False):
    import cv2
    root = Path(__file__).resolve().parents[2]
    profile = load_profile(root / "config" / "default_profile.json")
    adapter = PynputInputAdapter()
    layout = discover_monitors(profile.monitor_mode, profile.fixed_monitor)
    calibration_path = root / "data" / "mouse_calibration.json"
    calibration = load_calibration(calibration_path)
    mouse = MouseController(adapter, profile, layout, calibration)
    keyboard = GestureController(adapter, profile)
    camera, tracker = Camera(index=camera_index), MediaPipeTracker()
    overlay = Overlay(cv2)
    calibration_session = CalibrationSession()
    paused = start_paused
    last_log = 0.0
    try:
        camera.open()
        while True:
            frame = camera.read()
            frame = cv2.flip(frame, 1)
            result = tracker.track(frame, time.monotonic())
            mouse_hand, keyboard_hand = assign_roles(result, profile.mouse_hand,
                                                      profile.keyboard_hand,
                                                      profile.swap_hands)
            if calibration_session.active:
                mouse.release_all(); keyboard.release_all()
                mouse.status = "calibrating"
                gesture = f"calibrate:{calibration_session.stage}"
            elif not paused:
                mouse.update(mouse_hand, (result.width, result.height))
                gesture = keyboard.update(keyboard_hand)
            else:
                gesture = "paused"
            help_text = ""
            if calibration_session.active:
                help_text = f"Move right index to {calibration_session.stage}; SPACE=capture, R=cancel"
            overlay.draw(frame, paused=paused, mouse_role=profile.mouse_hand,
                         keyboard_role=profile.keyboard_hand, gesture=gesture,
                         hands=result.hands, mouse_found=mouse_hand is not None,
                         keyboard_found=keyboard_hand is not None,
                         mouse_status=mouse.status, monitor_name=mouse.target_region.name,
                         error=help_text)
            now = time.monotonic()
            if now - last_log >= 1.0:
                labels = [(h.label, round(h.confidence, 2)) for h in result.hands]
                print(f"[vision] camera={camera_index} swap_hands={profile.swap_hands} hands={labels} mouse_found={mouse_hand is not None} "
                      f"keyboard_found={keyboard_hand is not None} gesture={gesture} "
                      f"mouse_status={mouse.status} monitor={mouse.target_region.name}", flush=True)
                last_log = now
            cv2.imshow("VisionControl", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27: break
            if key in (ord("c"), ord("C")) and not calibration_session.active:
                calibration_session.start()
                mouse.release_all(); keyboard.release_all()
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
                if paused: mouse.release_all(); keyboard.release_all()
    except KeyboardInterrupt:
        pass
    finally:
        mouse.release_all(); keyboard.release_all(); adapter.release_all(); camera.close(); tracker.close(); cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VisionControl webcam controller")
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--start-paused", action="store_true")
    args = parser.parse_args()
    run(args.camera_index, args.start_paused)
