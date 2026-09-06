"""Explicit camera timing smoke test; never creates an input adapter or saves frames."""
import argparse
import statistics
import time

from vision_control.camera import Camera
from vision_control.tracker import MediaPipeTracker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--camera-index', type=int, default=0)
    parser.add_argument('--frames', type=int, default=60)
    args = parser.parse_args()
    if args.frames < 10:
        parser.error('--frames must be at least 10')
    camera = Camera(args.camera_index)
    tracker = None
    try:
        tracker = MediaPipeTracker()
        camera.open()
        durations = []
        started = time.perf_counter()
        for _ in range(args.frames):
            frame = camera.read()
            before = time.perf_counter()
            tracker.track(frame, time.monotonic())
            durations.append((time.perf_counter() - before) * 1000)
        print(f'Tracking median after warmup: {statistics.median(durations[5:]):.1f} ms')
        print(f'Capture + tracking: {args.frames / (time.perf_counter() - started):.1f} FPS')
    finally:
        camera.close()
        if tracker is not None:
            tracker.close()


if __name__ == '__main__':
    main()
