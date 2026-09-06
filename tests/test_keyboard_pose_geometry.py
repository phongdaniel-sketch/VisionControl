from dataclasses import replace
from pathlib import Path
import unittest

from tests.hand_geometry import pose, transformed
from tests.test_core import RecordingInput
from vision_control.controllers import GestureController
from vision_control.gestures import classify_static, thumb_state
from vision_control.profile import GestureBinding, load_profile


class KeyboardPoseGeometryTests(unittest.TestCase):
    def test_three_four_open_for_both_hands_mirrors_rotations_and_scale(self):
        for kind, expected in [('three', 'three_fingers'), ('four', 'four_fingers'), ('open', 'open_palm')]:
            for label in ('Left', 'Right'):
                for mirrored in (False, True):
                    for angle in (0, 30, 90, 180):
                        for scale in (.5, 1):
                            observation = transformed(pose(kind), angle, scale)
                            if mirrored:
                                observation = replace(observation, landmarks=tuple(
                                    (1-x, y, z) for x, y, z in observation.landmarks))
                            observation = replace(observation, label=label)
                            with self.subTest(kind=kind, label=label, mirrored=mirrored, angle=angle, scale=scale):
                                self.assertEqual(classify_static(observation)[0], expected)

    def uncertain_thumb(self):
        observation = pose('open')
        points = list(observation.landmarks)
        points[2], points[3], points[4] = (.40, .56, 0), (.365, .56, 0), (.3325, .56, 0)
        return replace(observation, landmarks=tuple(points))

    def test_uncertain_thumb_does_not_become_four_fingers(self):
        observation = self.uncertain_thumb()
        self.assertEqual(thumb_state(observation), 'unknown')
        self.assertEqual(classify_static(observation)[0], 'none')

    def test_default_keyboard_dispatch_distinguishes_d_s_space(self):
        profile = load_profile(Path(__file__).parents[1] / 'config/default_profile.json')
        adapter = RecordingInput()
        controller = GestureController(adapter, profile)
        for kind in ('three', 'four', 'open'):
            observation = replace(pose(kind), label='Left')
            for _ in range(4):
                controller.update(observation)
        self.assertEqual(adapter.events, [('press', 'd'), ('press', 's'), ('press', 'space')])

    def test_ambiguous_pose_releases_held_key(self):
        profile = load_profile(Path(__file__).parents[1] / 'config/default_profile.json')
        profile = replace(profile, bindings={'open_palm': GestureBinding('hold', ('shift',))})
        adapter = RecordingInput()
        controller = GestureController(adapter, profile)
        for _ in range(3):
            controller.update(pose('open'))
        controller.update(self.uncertain_thumb())
        self.assertEqual(adapter.events, [('key_down', 'shift'), ('key_up', 'shift')])

    def test_aspect_ratio_does_not_change_pose(self):
        for kind, expected in [('three', 'three_fingers'), ('four', 'four_fingers'), ('open', 'open_palm')]:
            observation = transformed(pose(kind), 45)
            wide = replace(observation, landmarks=tuple((x*.75, y, z*.75)
                           for x, y, z in observation.landmarks))
            self.assertEqual(classify_static(wide, (1280, 720))[0], expected)
