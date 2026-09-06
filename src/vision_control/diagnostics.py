"""Local diagnostic artifacts and simulated input. No desktop capture or OS input."""
from dataclasses import asdict
from datetime import datetime
import json
import math
from pathlib import Path
import statistics
import time
import uuid

from .input_adapter import InputAdapter
from .types import distance


PHASES = (
    (5, 'hold', 'Hold your pointing hand still for 5 seconds'),
    (10, 'move', 'Move slowly left/right and up/down'),
    (20, 'left_click', 'Aim at the circle; extend index, pinch, then release'),
    (25, 'right_click', 'Aim at the circle; extend middle, pinch, then release'),
    (30, 'keyboard', 'Left hand: show Three, Four, then Open palm'),
)


def phase_at(elapsed):
    return next(((name, text) for until, name, text in PHASES if elapsed < until),
                ('done', 'Recording complete'))


class DiagnosticInputAdapter(InputAdapter):
    """Runs the real controllers against a test pointer, never against the OS."""
    def __init__(self):
        self.cursor = (320.0, 240.0)
        self.held_buttons = set()
        self.held_keys = set()
        self.events = []

    def _event(self, action, **values):
        self.events.append({'time': time.monotonic(), 'action': action, **values})

    def move(self, x, y):
        self.cursor = (x, y)
        self._event('move', x=x, y=y)

    def position(self): return self.cursor
    def button_down(self, button):
        self.held_buttons.add(button)
        self._event('button_down', button=button, position=self.cursor)
    def button_up(self, button):
        self.held_buttons.discard(button)
        self._event('button_up', button=button, position=self.cursor)
    def scroll(self, amount): self._event('scroll', amount=amount)
    def scroll_xy(self, x, y): self._event('scroll_xy', x=x, y=y)
    def key_press(self, key): self._event('key_press', key=key)
    def key_down(self, key):
        self.held_keys.add(key)
        self._event('key_down', key=key)
    def key_up(self, key):
        self.held_keys.discard(key)
        self._event('key_up', key=key)
    def release_all(self):
        for button in tuple(self.held_buttons): self.button_up(button)
        for key in tuple(self.held_keys): self.key_up(key)
    def drain(self):
        events, self.events = self.events, []
        return events


def frame_record(runtime, snapshot, events, elapsed):
    mouse = runtime.mouse
    from .roles import assign_roles
    from .types import HandsFrame
    hand, _ = assign_roles(HandsFrame(0, snapshot.hands), runtime.profile.mouse_hand,
                           runtime.profile.keyboard_hand, runtime.profile.swap_hands)
    ratios = {}
    if hand is not None:
        palm = max(distance(hand.landmarks[0], hand.landmarks[9]), .001)
        ratios = {name: distance(hand.landmarks[4], hand.landmarks[tip]) / palm
                  for name, tip in [('index', 8), ('middle', 12)]}
    for event in events:
        if event['action'] == 'button_down':
            event['target_distance_px'] = math.dist(event['position'], (320, 240))
            event['target_hit'] = event['target_distance_px'] <= 35
    return {
        'sample_time': snapshot.sample_time, 'elapsed_s': elapsed,
        'frame_size': [snapshot.frame.shape[1], snapshot.frame.shape[0]],
        'phase': phase_at(elapsed)[0], 'mouse_pose': snapshot.mouse_pose,
        'keyboard_pose': snapshot.keyboard_pose, 'mouse_found': snapshot.mouse_found,
        'keyboard_found': snapshot.keyboard_found, 'mouse_status': snapshot.mouse_status,
        'keyboard_state': snapshot.keyboard_state, 'pinch_ratios': ratios,
        'pinch_decision': mouse.pinch_decision, 'pending_pinch': mouse.pending_pinch,
        'cursor': runtime.adapter.position(), 'events': events,
        'hands': [asdict(hand) for hand in snapshot.hands],
        'timings_ms': dict(snapshot.timings_ms),
    }


def render_composite(snapshot, adapter, elapsed, recording, frame_number, pointer_mode=None, gesture_v1=False):
    import cv2
    import numpy as np
    result = np.zeros((560, 1280, 3), dtype=np.uint8)
    result[:] = (23, 17, 12)
    result[:480, :640] = cv2.resize(snapshot.frame, (640, 480))
    for x in range(640, 1280, 80): cv2.line(result, (x, 0), (x, 480), (50, 43, 37))
    for y in range(0, 481, 80): cv2.line(result, (640, y), (1279, y), (50, 43, 37))
    cv2.circle(result, (960, 240), 35, (90, 180, 250), 2)
    x, y = adapter.position()
    point = (640 + round(max(0, min(639, x))), round(max(0, min(479, y))))
    color = (70, 70, 250) if adapter.held_buttons else (90, 255, 100)
    cv2.circle(result, point, 9, color, -1)
    cv2.putText(result, 'TEST POINTER - NO OS INPUT', (655, 25), cv2.FONT_HERSHEY_SIMPLEX, .6, (255,255,255), 1)
    state = 'REC' if recording else 'PAUSED / PREVIEW'
    lines = [f'{state} | {elapsed:05.2f}s | frame {frame_number} | Mouse: {snapshot.mouse_pose} | Key: {snapshot.keyboard_pose}',
             phase_at(elapsed)[1] if recording else 'Press Start recording when ready. Webcam + test area only.']
    if recording and pointer_mode == 'thumb_lock':
        lines[1] = {
            'hold': 'Thumb tucked: hold index still',
            'move': 'Thumb tucked: move index; open thumb to lock',
            'left_click': 'Thumb open: curl index then extend; middle alone = middle click',
            'right_click': 'Thumb open: curl index + middle together, then extend both',
            'keyboard': 'Separate thumb/index, pinch to drag, move palm, release',
        }.get(phase_at(elapsed)[0], 'Done')
    if recording and gesture_v1:
        lines[1] = f'V1 | Mouse: {snapshot.mouse_status} | Second hand: {snapshot.keyboard_state}'
    for index, line in enumerate(lines):
        cv2.putText(result, line, (15, 510 + index*28), cv2.FONT_HERSHEY_SIMPLEX, .57, (230,230,230), 1)
    return result


class DiagnosticRecorder:
    duration = 30.0
    video_fps = 30.0

    def __init__(self, root, metadata, *, clock=time.monotonic, writer_factory=None):
        import cv2
        self.clock = clock
        self.started = clock()
        self.count = 0
        self.closed = False
        self.writer = self.log = None
        self.directory = Path(root) / (datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8])
        self.directory.mkdir(parents=True)
        try:
            self.metadata = {**metadata, 'started_monotonic': self.started,
                'duration_limit_s': self.duration, 'video_nominal_fps': self.video_fps,
                'input_mode': 'simulated; no OS input',
                'time_mapping': 'AVI frame N corresponds to JSONL video_frame N; use elapsed_s, not playback time',
                'sensor_latency': 'not measured; sample_time is after camera.read returns'}
            (self.directory / 'metadata.json').write_text(json.dumps(self.metadata, indent=2), encoding='utf-8')
            factory = writer_factory or cv2.VideoWriter
            self.writer = factory(str(self.directory / 'session.avi'), cv2.VideoWriter_fourcc(*'MJPG'),
                                  self.video_fps, (1280, 560))
            if not self.writer.isOpened():
                raise RuntimeError('Unable to create diagnostic AVI writer')
            self.log = (self.directory / 'frames.jsonl').open('w', encoding='utf-8')
        except Exception:
            if self.writer is not None: self.writer.release()
            if self.log is not None: self.log.close()
            raise

    @property
    def elapsed(self): return max(0.0, self.clock() - self.started)

    def append(self, frame, record):
        if self.closed or self.elapsed >= self.duration:
            return False
        record = {**record, 'video_frame': self.count, 'write_elapsed_s': self.elapsed,
                  'timings_ms': dict(record.get('timings_ms', {}))}
        json.dumps(record, allow_nan=False)
        before = time.perf_counter()
        self.writer.write(frame)
        record['timings_ms']['video_write'] = (time.perf_counter() - before) * 1000
        self.log.write(json.dumps(record, allow_nan=False) + '\n')
        self.log.flush()
        self.count += 1
        return True

    def close(self, reason='stopped', final_events=()):
        if self.closed: return
        self.closed = True
        try:
            if self.writer is not None: self.writer.release()
        finally:
            if self.log is not None: self.log.close()
        summary = summarize(self.directory)
        summary.update(stop_reason=reason, elapsed_wall_s=self.elapsed, final_release_events=list(final_events))
        (self.directory / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')


def summarize(directory):
    path = Path(directory) / 'frames.jsonl'
    records = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    timing_keys = {key for row in records for key in row.get('timings_ms', {})}
    timing = {key: round(statistics.median([row['timings_ms'][key] for row in records
                                          if key in row.get('timings_ms', {})]), 2) for key in timing_keys}
    span = records[-1]['elapsed_s'] - records[0]['elapsed_s'] if len(records) > 1 else 0
    clicks = [{'frame': row['video_frame'], 'elapsed_s': row['elapsed_s'], 'phase': row['phase'], **event}
              for row in records for event in row['events'] if event['action'] == 'button_down']
    return {'frames': len(records), 'processed_fps': round((len(records)-1)/span, 2) if span else 0,
            'mouse_missing_frames': sum(not row['mouse_found'] for row in records),
            'median_stage_ms': timing, 'simulated_clicks': clicks,
            'note': 'Target hits reflect simulated controller output, not OS click delivery or confirmed user intent.'}
