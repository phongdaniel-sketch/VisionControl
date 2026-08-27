import argparse
import time
from pathlib import Path
from .camera import Camera
from .controllers import GestureController, MouseController
from .input_adapter import PynputInputAdapter
from .profile import load_profile
from .tracker import MediaPipeTracker
from .overlay import Overlay
from .roles import assign_roles


def run(camera_index=0):
    import cv2
    root = Path(__file__).resolve().parents[2]
    profile = load_profile(root / "config" / "default_profile.json")
    adapter = PynputInputAdapter()
    mouse = MouseController(adapter, profile)
    keyboard = GestureController(adapter, profile)
    camera, tracker = Camera(index=camera_index), MediaPipeTracker()
    overlay = Overlay(cv2)
    paused = False
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
            if not paused: mouse.update(mouse_hand, (result.width, result.height))
            gesture = keyboard.update(keyboard_hand) if not paused else "paused"
            overlay.draw(frame, paused=paused, mouse_role=profile.mouse_hand,
                         keyboard_role=profile.keyboard_hand, gesture=gesture,
                         hands=result.hands, mouse_found=mouse_hand is not None,
                         keyboard_found=keyboard_hand is not None)
            now = time.monotonic()
            if now - last_log >= 1.0:
                labels = [(h.label, round(h.confidence, 2)) for h in result.hands]
                print(f"[vision] camera={camera_index} swap_hands={profile.swap_hands} hands={labels} mouse_found={mouse_hand is not None} "
                      f"keyboard_found={keyboard_hand is not None} gesture={gesture} "
                      f"mouse_paused={mouse.paused}", flush=True)
                last_log = now
            cv2.imshow("VisionControl", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27: break
            if key in (ord("p"), ord("P")):
                paused = not paused
                if paused: mouse.release_all(); keyboard.release_all()
    finally:
        mouse.release_all(); keyboard.release_all(); adapter.release_all(); camera.close(); tracker.close(); cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VisionControl webcam controller")
    parser.add_argument("--camera-index", type=int, default=0)
    args = parser.parse_args()
    run(args.camera_index)
