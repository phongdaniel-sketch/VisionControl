"""Explicit local webcam experiment: no OS input and no saved camera images."""
import argparse
from collections import Counter
import json
from pathlib import Path
import statistics
import subprocess
import sys
import threading
import time


def run_case(mode, width, height, fps):
    import cv2
    from vision_control.tracker import MediaPipeTracker
    stop = threading.Event()
    condition = threading.Condition()
    shared = {'latest': None, 'error': None, 'metadata': None}
    capture_times = []

    def open_camera():
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        try:
            if not cap.isOpened():
                raise RuntimeError('Camera unavailable')
            # Apply the codec last: size/FPS negotiation may reset the format.
            accepted = [cap.set(cv2.CAP_PROP_FRAME_WIDTH, width),
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height),
                        cap.set(cv2.CAP_PROP_FPS, fps),
                        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))]
            code = int(cap.get(cv2.CAP_PROP_FOURCC))
            shared['metadata'] = {
                'backend': cap.getBackendName(), 'set_accepted': accepted,
                'driver_fps': cap.get(cv2.CAP_PROP_FPS),
                'reported_exposure': cap.get(cv2.CAP_PROP_EXPOSURE),
                'reported_auto_exposure': cap.get(cv2.CAP_PROP_AUTO_EXPOSURE),
                'reported_gain': cap.get(cv2.CAP_PROP_GAIN),
                'fourcc': ''.join(chr((code >> (8*i)) & 255) for i in range(4)),
            }
            return cap
        except Exception:
            cap.release()
            raise

    def read(cap):
        before = time.monotonic()
        ok, frame = cap.read()
        after = time.monotonic()
        if not ok:
            raise RuntimeError('Camera read failed')
        return frame, after, (after-before)*1000

    def reader():
        cap = None
        try:
            cap = open_camera()
            sequence = 0
            while not stop.is_set():
                frame, stamp, read_ms = read(cap)
                sequence += 1
                with condition:
                    capture_times.append(stamp)
                    shared['latest'] = (sequence, frame, stamp, read_ms)
                    condition.notify_all()
        except Exception as exc:
            with condition:
                shared['error'] = str(exc)
                condition.notify_all()
        finally:
            if cap is not None:
                cap.release()

    tracker = None if mode == 'camera' else MediaPipeTracker()
    worker = cap = None
    records = []
    last_sequence = 0
    try:
        if mode == 'latest':
            worker = threading.Thread(target=reader, daemon=True)
            worker.start()
        else:
            cap = open_camera()
        first = None
        while True:
            if mode == 'latest':
                with condition:
                    available = condition.wait_for(lambda: shared['error'] or (
                        shared['latest'] is not None and shared['latest'][0] > last_sequence),
                        timeout=20 if first is None else 5)
                    if not available or shared['error']:
                        raise RuntimeError(shared['error'] or 'Camera startup/frame wait timed out')
                    sequence, frame, stamp, read_ms = shared['latest']
            else:
                frame, stamp, read_ms = read(cap)
                capture_times.append(stamp)
                sequence = last_sequence + 1
            last_sequence = sequence
            if first is None:
                first = stamp
            if stamp-first >= 7:
                break
            start_tracking = time.monotonic()
            hands = None
            if tracker:
                result = tracker.track(cv2.flip(frame, 1), stamp)
                hands = len(result.hands)
            end = time.monotonic()
            if stamp-first >= 1:
                records.append({'sequence': sequence, 'read_ms': read_ms,
                    'tracking_ms': (end-start_tracking)*1000,
                    'post_read_age_ms': (end-stamp)*1000,
                    'time': end, 'hands': hands})
        captured = [t for t in capture_times if first+1 <= t < first+7]
        def rate(times):
            return round((len(times)-1)/(times[-1]-times[0]), 2) if len(times)>1 else 0
        output = {'mode': mode, 'requested': [width,height,fps],
            **shared['metadata'], 'actual_size': [frame.shape[1],frame.shape[0]],
            'camera_read_fps': rate(captured), 'completed_fps': rate([r['time'] for r in records]),
            'processed_frames': len(records),
            'skipped_sequence_ids': sum(b['sequence']-a['sequence']-1 for a,b in zip(records,records[1:])),
            'hand_count_histogram': dict(Counter(r['hands'] for r in records)),
            'note': 'Read completions, not verified distinct sensor exposures. Age starts after read, not exposure. No GUI/input/recording.'}
        for key in ('read_ms','tracking_ms','post_read_age_ms'):
            values = sorted(r[key] for r in records)
            output[key] = {'median': round(statistics.median(values),2),
                           'p95': round(values[min(len(values)-1,int(len(values)*.95))],2)}
        return output
    finally:
        stop.set()
        if worker:
            worker.join(5)
        if cap is not None:
            cap.release()
        if tracker:
            tracker.close()
        if worker and worker.is_alive():
            raise RuntimeError('Camera worker did not shut down; isolated process will exit')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['camera','sequential','latest'])
    parser.add_argument('--width', type=int, default=640)
    parser.add_argument('--height', type=int, default=480)
    parser.add_argument('--fps', type=int, default=30)
    args = parser.parse_args()
    if args.case:
        print(json.dumps(run_case(args.case,args.width,args.height,args.fps)),flush=True)
        return
    results = []
    path = Path('build/pipeline-experiment.json')
    path.parent.mkdir(exist_ok=True)
    for repeat in range(2):
        for width,height,fps in [(640,480,30),(1280,720,60)]:
            modes = ['camera','sequential','latest'] if repeat == 0 else ['latest','sequential','camera']
            for mode in modes:
                print(f'TEST pass={repeat+1} {width}x{height}/{fps} {mode}',flush=True)
                try:
                    child = subprocess.run([sys.executable,__file__,'--case',mode,
                        '--width',str(width),'--height',str(height),'--fps',str(fps)],
                        capture_output=True,text=True,timeout=35)
                    if child.returncode:
                        raise RuntimeError(child.stderr[-1500:])
                    row = json.loads(child.stdout.strip().splitlines()[-1])
                    row['repeat'] = repeat+1
                except Exception as exc:
                    row = {'repeat': repeat+1,'mode': mode,'requested':[width,height,fps],'error':str(exc)}
                results.append(row)
                path.write_text(json.dumps(results,indent=2),encoding='utf-8')
                print(json.dumps(row),flush=True)


if __name__ == '__main__':
    main()
