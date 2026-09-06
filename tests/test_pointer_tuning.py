import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tests.test_core import RecordingInput, hand
from tests.hand_geometry import pose
from vision_control.controllers import MouseController
from vision_control.profile import load_profile


class PointerTuningTests(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile(Path(__file__).parents[1] / 'config/default_profile.json')

    def run_frames(self, controller, pinches, times):
        observation = hand((True, False, False, False))
        # Supply the real open-hand preparation required before any new pinch.
        if not controller.pinch_ready_at:
            with patch('vision_control.controllers.time.monotonic', return_value=times[0]-.01):
                controller.update(pose('open'))
        with patch('vision_control.controllers.time.monotonic', side_effect=times):
            for left, right in pinches:
                def pinch(_hand, gesture, _close, _open, _active):
                    return left if gesture == 'pinch_index' else right if gesture == 'pinch_middle' else False
                with patch.object(controller, '_configured_pinch', side_effect=pinch):
                    controller.update(observation)

    def test_brief_pinch_is_rejected_and_stable_pinch_clicks_once(self):
        adapter = RecordingInput()
        controller = MouseController(adapter, self.profile)
        self.run_frames(controller, [(True, False), (False, False), (True, False),
                                     (True, False), (True, False), (False, False)],
                        [0, .04, .1, .19, .3, .31])
        self.assertEqual([e for e in adapter.events if e[0] in ('down', 'up')],
                         [('down', 'left'), ('up', 'left')])

    def test_ambiguous_pinch_never_clicks(self):
        adapter = RecordingInput()
        controller = MouseController(adapter, self.profile)
        self.run_frames(controller, [(True, True)] * 3, [0, .2, .4])
        self.assertFalse(any(e[0] == 'down' for e in adapter.events))

    def test_cannot_switch_to_right_until_both_pinches_open(self):
        adapter = RecordingInput()
        controller = MouseController(adapter, self.profile)
        self.run_frames(controller,
                        [(True, False), (True, False), (True, True), (False, True),
                         (False, True), (False, False), (False, True), (False, True)],
                        [0, .1, .2, .3, .5, .6, .7, .8])
        self.assertEqual([e for e in adapter.events if e[0] in ('down', 'up')],
                         [('down', 'left'), ('up', 'left'), ('down', 'right')])

    def test_pause_clears_pending_click(self):
        adapter = RecordingInput()
        controller = MouseController(adapter, self.profile)
        self.run_frames(controller, [(True, False)], [0])
        controller.release_all()
        self.run_frames(controller, [(True, False)], [1])
        self.assertFalse(any(e[0] == 'down' for e in adapter.events))

    def test_folded_middle_finger_cannot_start_pinch(self):
        adapter = RecordingInput()
        controller = MouseController(adapter, self.profile)
        with patch('vision_control.controllers.time.monotonic', side_effect=[0, .1, .2]):
            for _ in range(3):
                controller.update(pose('middle_pinch'))
        self.assertFalse(any(event[0] == 'down' for event in adapter.events))

    def test_adaptive_filter_reduces_small_motion_and_catches_large_motion(self):
        profile = replace(self.profile, thresholds={**self.profile.thresholds,
            'cursor_adaptive_smoothing': True, 'cursor_smoothing': .6})
        for offset, minimum, maximum in [(4, 0, 2.4), (100, 99, 101)]:
            adapter = RecordingInput()
            controller = MouseController(adapter, profile)
            controller.last = (100, 100)
            controller.last_move_time = 0
            with patch.object(controller.calibration, 'map_to_region', return_value=(100 + offset, 100)), \
                    patch('vision_control.controllers.time.monotonic', return_value=1 / 30):
                controller.update(hand((True, False, False, False)))
            self.assertGreater(controller.last[0] - 100, minimum)
            self.assertLess(controller.last[0] - 100, maximum)

    def test_video_timestamps_strictly_increase(self):
        import numpy as np
        from vision_control.tracker import MediaPipeTracker
        tracker = object.__new__(MediaPipeTracker)
        tracker.mp = SimpleNamespace(Image=Mock(), ImageFormat=SimpleNamespace(SRGB=1))
        tracker.landmarker = Mock()
        tracker.landmarker.detect_for_video.return_value = SimpleNamespace(
            hand_landmarks=[], handedness=[])
        tracker.last_timestamp_ms = -1
        for timestamp in [0, 0, .0001, 1]:
            tracker.track(np.zeros((10, 10, 3), dtype=np.uint8), timestamp)
        self.assertEqual([call.args[1] for call in tracker.landmarker.detect_for_video.call_args_list],
                         [0, 1, 2, 1000])

    def test_invalid_tuning_is_rejected(self):
        raw = json.loads((Path(__file__).parents[1] / 'config/default_profile.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'profile.json'
            for name, value in [('pinch_confirm_seconds', -.1), ('cursor_smoothing', 2),
                                ('cursor_adaptive_smoothing', 'yes')]:
                changed = json.loads(json.dumps(raw))
                changed['thresholds'][name] = value
                path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    load_profile(path)
