from dataclasses import replace
import math
from pathlib import Path
import unittest
from unittest.mock import patch

from tests.hand_geometry import pose
from vision_control.controllers import MouseController
from vision_control.diagnostics import DiagnosticInputAdapter
from vision_control.gestures import classify_mouse_pose, classify_static
from vision_control.profile import load_profile


class PointerRecoveryTests(unittest.TestCase):
    def test_relaxed_unused_finger_is_mouse_point_but_not_keyboard_point(self):
        hand = pose('point')
        points = list(hand.landmarks)
        points[12] = (.56, .38, 0)
        hand = replace(hand, landmarks=tuple(points))
        self.assertEqual(classify_static(hand)[0], 'none')
        self.assertEqual(classify_mouse_pose(hand), 'point')
        self.assertEqual(classify_mouse_pose(pose('fist')), 'fist')
        self.assertNotEqual(classify_mouse_pose(pose('open')), 'point')

    def test_recovery_is_bounded_and_converges_without_click(self):
        profile = load_profile(Path(__file__).parents[1] / 'config/default_profile.json')
        profile = replace(profile, pointer_mode='index_fingertip')
        adapter = DiagnosticInputAdapter()
        controller = MouseController(adapter, profile, screen=(640, 480))
        with patch('vision_control.controllers.time.monotonic', return_value=0):
            controller.update(pose('point'))
        with patch('vision_control.controllers.time.monotonic', return_value=.1):
            controller.update(pose('open'))
        previous = adapter.position()
        shifted = replace(pose('point'), landmarks=tuple((x+.4, y+.4, z) for x,y,z in pose('point').landmarks))
        for index in range(20):
            with patch('vision_control.controllers.time.monotonic', return_value=1+index/30):
                controller.update(shifted)
            self.assertLessEqual(math.dist(previous, adapter.position()), 96.0001)
            previous = adapter.position()
        target = controller.calibration.map(shifted.landmarks[8][0], shifted.landmarks[8][1], (640,480))
        self.assertLess(math.dist(adapter.position(), target), 2)
        self.assertFalse(adapter.held_buttons)
        controller.update(None)
        self.assertFalse(controller.recovering_pointer)
