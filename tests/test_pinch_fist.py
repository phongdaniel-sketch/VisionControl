from dataclasses import replace
from pathlib import Path
import unittest
from unittest.mock import patch

from tests.hand_geometry import pose, transformed
from tests.test_core import RecordingInput
from vision_control.controllers import MouseController
from vision_control.gestures import is_closed_fist, finger_extended, classify_mouse_pose
from vision_control.profile import load_profile
from vision_control.runtime import VisionRuntime


class PinchFistTests(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile(Path(__file__).parents[1] / 'config/default_profile.json')
        self.adapter = RecordingInput()
        self.controller = MouseController(self.adapter, self.profile)

    def step(self, kind, now):
        with patch('vision_control.controllers.time.monotonic', return_value=now):
            self.controller.update(pose(kind) if kind else None)

    def button_events(self):
        return [e for e in self.adapter.events if e[0] in ('down', 'up')]

    def test_pinch_below_pip_is_not_a_fist_across_scale_and_rotation(self):
        pinching = pose('pinch')
        self.assertTrue(all(pinching.landmarks[tip][1] >= pinching.landmarks[tip-2][1]
                            for tip in (8, 12, 16, 20)))
        for angle in (0, 45, 90, 180):
            for scale in (.5, 1, 1.3):
                with self.subTest(angle=angle, scale=scale):
                    self.assertFalse(is_closed_fist(transformed(pinching, angle, scale)))
                    self.assertTrue(is_closed_fist(transformed(pose('fist'), angle, scale)))
                    self.assertTrue(finger_extended(transformed(pose('point'), angle, scale), 8))

    def test_point_then_bent_pinch_clicks_and_holds_past_preparation_timeout(self):
        self.step('point', 0)
        self.step('pinch', .1)
        self.assertEqual(self.button_events(), [])
        self.step('pinch', .2)
        self.step('pinch', 2)
        self.assertEqual(self.button_events(), [('down', 'left')])
        self.step('point', 2.1)
        self.assertEqual(self.button_events(), [('down', 'left'), ('up', 'left')])

    def test_already_pinched_at_start_does_not_click(self):
        self.step('pinch', 0)
        self.step('pinch', 1)
        self.assertEqual(self.button_events(), [])

    def test_clear_fist_releases_and_cannot_turn_into_click(self):
        self.step('point', 0)
        self.step('pinch', .1)
        self.step('pinch', .2)
        self.step('fist', .21)
        self.step('pinch', .3)
        self.step('pinch', .5)
        self.assertEqual(self.button_events(), [('down', 'left'), ('up', 'left')])

    def test_pause_and_hand_loss_require_new_preparation(self):
        for reset in ('pause', 'loss'):
            with self.subTest(reset=reset):
                self.setUp()
                self.step('point', 0)
                self.step('pinch', .1)
                self.step('pinch', .2)
                if reset == 'pause':
                    runtime = VisionRuntime()
                    runtime.mouse = self.controller
                    runtime.set_paused(True)
                else:
                    self.step(None, .21)
                self.step('pinch', .3)
                self.step('pinch', .5)
                self.assertEqual(self.button_events(), [('down', 'left'), ('up', 'left')])

    def test_preparation_expires_before_new_pinch(self):
        self.step('point', 0)
        self.step('pinch', 1)
        self.step('pinch', 1.2)
        self.assertEqual(self.button_events(), [])

    def test_button_swap_uses_finger_preparation_not_button_name(self):
        self.controller = MouseController(self.adapter, replace(self.profile, thresholds={
            **self.profile.thresholds, 'mouse_primary_click_gesture': 'pinch_middle',
            'mouse_secondary_click_gesture': 'pinch_index'}))
        self.step('point', 0)
        self.step('pinch', .1)
        self.step('pinch', .2)
        self.assertEqual(self.button_events(), [('down', 'right')])

    def test_middle_finger_can_bend_after_preparation(self):
        self.step('middle', 0)
        self.step('middle_pinch', .1)
        self.step('middle_pinch', .2)
        self.assertEqual(self.button_events(), [('down', 'right')])

    def test_degenerate_geometry_is_not_confident_fist_or_extended_finger(self):
        hand = replace(pose(), landmarks=((.5, .5, 0),) * 21)
        self.assertFalse(is_closed_fist(hand))
        self.assertFalse(finger_extended(hand, 8))
        self.assertNotEqual(classify_mouse_pose(pose('pinch')), 'fist')
