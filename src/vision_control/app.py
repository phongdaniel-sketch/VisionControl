import argparse
from pathlib import Path
from .startup import StartupCancelled, StartupScreen
from .paths import resource_root
from .runtime import VisionRuntime


def run(camera_index=0, start_paused=False, profile_path=None):
    import cv2
    root = resource_root()
    startup = None
    runtime = VisionRuntime(camera_index, start_paused, profile_path)
    try:
        startup = StartupScreen(cv2, root / "docs" / "Splash Screen.png",
                                root / "docs" / "Loading Screen.png")
        startup.show_splash(1000)
        runtime.start(lambda value, message:
                      startup.show_loading(value, message,
                                           250 if value >= 1 else 1))
        while True:
            snapshot = runtime.process_frame(status_overlay=True)
            cv2.imshow("VisionControl", snapshot.frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27: break
            if key in (ord("c"), ord("C")):
                runtime.start_calibration()
            elif key == ord(" "):
                runtime.capture_calibration()
            elif key in (ord("r"), ord("R")):
                runtime.cancel_calibration()
            elif key in (ord("p"), ord("P")):
                runtime.toggle_paused()
    except (KeyboardInterrupt, StartupCancelled):
        pass
    except Exception as exc:
        print(f"[startup] failed: {exc}", flush=True)
        try:
            if startup is not None:
                startup.show_loading(1.0, f"Failed: {exc}", 1500)
        except Exception:
            pass
        raise
    finally:
        runtime.close()
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
