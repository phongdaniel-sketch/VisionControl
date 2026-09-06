from dataclasses import replace
from pathlib import Path
import unittest
from unittest.mock import patch

from tests.hand_geometry import pose
from vision_control.controllers import MouseController
from vision_control.diagnostics import DiagnosticInputAdapter
from vision_control.gestures import classify_mouse_pose, finger_extended
from vision_control.profile import load_profile


class AimClickTests(unittest.TestCase):
    def setUp(self):
        profile = load_profile(Path(__file__).parents[1] / 'config/default_profile.json')
        self.profile = replace(profile, thresholds={**profile.thresholds, 'cursor_adaptive_smoothing': True})
        self.adapter = DiagnosticInputAdapter()
        self.controller = MouseController(self.adapter, self.profile, screen=(640, 480))

    def step(self, hand, now):
        with patch('vision_control.controllers.time.monotonic', return_value=now):
            self.controller.update(hand)

    def test_click_stays_at_aimed_position(self):
        self.step(pose('point'), 0)
        aimed = self.adapter.position()
        self.step(pose('pinch'), .1)
        self.step(pose('pinch'), .2)
        self.assertEqual(self.adapter.position(), aimed)
        self.assertEqual(self.adapter.held_buttons, {'left'})
        click = next(e for e in self.adapter.events if e['action'] == 'button_down')
        self.assertEqual(click['position'], aimed)
        self.step(None, .3)
        self.assertFalse(self.adapter.held_buttons)

    def test_resting_jitter_is_held_but_deliberate_motion_moves(self):
        original = pose('point')
        self.step(original, 0)
        aimed = self.adapter.position()
        for i in range(1, 12):
            pts = list(original.landmarks)
            x,y,z = pts[8]
            pts[8] = (x + (-1)**i * .0005, y, z)
            self.step(replace(original, landmarks=tuple(pts)), i/30)
            self.assertEqual(self.adapter.position(), aimed)
        for i in range(12, 24):
            pts = list(original.landmarks)
            x,y,z = pts[8]
            pts[8] = (x + .001 * (i-11), y, z)
            self.step(replace(original, landmarks=tuple(pts)), i/30)
        self.assertGreater(self.adapter.position()[0], aimed[0]+2)

    def test_moderately_bent_index_is_mouse_point_only(self):
        hand = pose('point')
        pts = list(hand.landmarks)
        pts[8] = (.49, .20, 0)
        hand = replace(hand, landmarks=tuple(pts))
        self.assertFalse(finger_extended(hand, 8))
        self.assertEqual(classify_mouse_pose(hand), 'point')
        self.assertEqual(classify_mouse_pose(pose('fist')), 'fist')
