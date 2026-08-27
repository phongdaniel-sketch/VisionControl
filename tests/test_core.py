import json
import tempfile
import unittest
from pathlib import Path

from vision_control.controllers import GestureController, MouseController
from vision_control.profile import load_profile
from vision_control.types import HandObservation
from vision_control.calibration import MouseCalibration
from vision_control.input_adapter import PynputInputAdapter
from vision_control.roles import assign_roles
from vision_control.types import HandsFrame


class RecordingInput:
    def __init__(self): self.events = []
    def move(self, x, y): self.events.append(("move", x, y))
    def button_down(self, b): self.events.append(("down", b))
    def button_up(self, b): self.events.append(("up", b))
    def scroll(self, n): self.events.append(("scroll", n))
    def key_press(self, k): self.events.append(("press", k))
    def key_down(self, k): self.events.append(("key_down", k))
    def key_up(self, k): self.events.append(("key_up", k))
    def release_all(self): self.events.append(("release_all",))


def hand(states=(False, False, False, False), label="Left"):
    points = [(0.5, .5, 0.0)] * 21
    for tip, pip, up in zip((8, 12, 16, 20), (6, 10, 14, 18), states):
        points[pip] = (.5, .5, 0); points[tip] = (.5, .3 if up else .7, 0)
    points[0] = (.5, .5, 0); points[9] = (.5, .7, 0)
    return HandObservation(label, tuple(points))


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile(Path(__file__).parents[1] / "config/default_profile.json")

    def test_profile_loads_and_has_two_roles(self):
        self.assertNotEqual(self.profile.mouse_hand, self.profile.keyboard_hand)
        self.assertTrue(self.profile.swap_hands)
        self.assertEqual(self.profile.bindings["point"].keys, ("w",))

    def test_keyboard_press_is_debounced(self):
        adapter = RecordingInput(); controller = GestureController(adapter, self.profile)
        point = hand((True, False, False, False))
        for _ in range(5): controller.update(point)
        self.assertEqual([e for e in adapter.events if e == ("press", "w")], [("press", "w")])

    def test_held_binding_releases_when_gesture_disappears(self):
        adapter = RecordingInput(); controller = GestureController(adapter, self.profile)
        fist = hand((False, False, False, False))
        for _ in range(3): controller.update(fist)
        controller.update(None)
        self.assertIn(("key_down", "shift"), adapter.events)
        self.assertIn(("key_up", "shift"), adapter.events)

    def test_held_binding_releases_when_switching_gesture(self):
        adapter = RecordingInput(); controller = GestureController(adapter, self.profile)
        fist = hand((False, False, False, False)); point = hand((True, False, False, False))
        for _ in range(3): controller.update(fist)
        for _ in range(3): controller.update(point)
        self.assertIn(("key_up", "shift"), adapter.events)
        self.assertIn(("press", "w"), adapter.events)

    def test_mouse_fist_releases_buttons(self):
        adapter = RecordingInput(); controller = MouseController(adapter, self.profile)
        controller.left_down = True
        controller.update(hand((False, False, False, False), "Right"))
        self.assertIn(("up", "left"), adapter.events)

    def test_invalid_profile_rejected(self):
        raw = {"version": 1, "mouse_hand": "Right", "keyboard_hand": "Right", "left_hand": {}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"; path.write_text(json.dumps(raw))
            with self.assertRaises(ValueError): load_profile(path)

    def test_calibration_maps_active_region_to_screen(self):
        calibration = MouseCalibration(.1, .9, .1, .9)
        self.assertEqual(calibration.map(.1, .1, (1000, 500)), (0.0, 0.0))
        self.assertEqual(calibration.map(.9, .9, (1000, 500)), (999.0, 499.0))

    def test_special_key_names_are_resolved(self):
        adapter = object.__new__(PynputInputAdapter)
        sentinel = object()
        adapter.keys = {"space": sentinel}
        self.assertIs(adapter._key("space"), sentinel)
        self.assertEqual(adapter._key("w"), "w")

    def test_hand_roles_can_be_swapped_for_mirrored_camera(self):
        raw_left = hand(label="Left")
        raw_right = hand(label="Right")
        frame = HandsFrame(0.0, (raw_left, raw_right))
        mouse, keyboard = assign_roles(frame, "Right", "Left", swap_hands=True)
        self.assertEqual(mouse.label, "Left")
        self.assertEqual(keyboard.label, "Right")


if __name__ == "__main__": unittest.main()
