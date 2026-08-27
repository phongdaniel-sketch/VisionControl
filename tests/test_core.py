import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from vision_control.controllers import GestureController, MouseController
from vision_control.profile import GestureBinding, load_profile
from vision_control.types import HandObservation
from vision_control.calibration import CalibrationSession, MouseCalibration
from vision_control.input_adapter import PynputInputAdapter
from vision_control.roles import assign_roles
from vision_control.types import HandsFrame
from vision_control.monitors import MonitorLayout, ScreenRegion
from vision_control.arming import ArmingController, ArmingSettings
from vision_control.startup import StartupScreen
from vision_control.settings import (DesktopSettings, load_desktop_settings,
                                     save_desktop_settings, save_user_profile)


class RecordingInput:
    def __init__(self): self.events = []; self._position = (0.0, 0.0)
    def move(self, x, y): self._position = (x, y); self.events.append(("move", x, y))
    def position(self): return self._position
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
        self.assertEqual(self.profile.monitor_mode, "active")
        self.assertTrue(self.profile.arming.enabled)
        self.assertNotIn("fist", self.profile.bindings)
        self.assertEqual(self.profile.bindings["point"].keys, ("w",))

    def test_keyboard_press_is_debounced(self):
        adapter = RecordingInput(); controller = GestureController(adapter, self.profile)
        point = hand((True, False, False, False))
        for _ in range(5): controller.update(point)
        self.assertEqual([e for e in adapter.events if e == ("press", "w")], [("press", "w")])

    def test_held_binding_releases_when_gesture_disappears(self):
        profile = replace(self.profile, bindings={**self.profile.bindings,
                                                  "fist": GestureBinding("hold", ("shift",))})
        adapter = RecordingInput(); controller = GestureController(adapter, profile)
        fist = hand((False, False, False, False))
        for _ in range(3): controller.update(fist)
        controller.update(None)
        self.assertIn(("key_down", "shift"), adapter.events)
        self.assertIn(("key_up", "shift"), adapter.events)

    def test_held_binding_releases_when_switching_gesture(self):
        profile = replace(self.profile, bindings={**self.profile.bindings,
                                                  "fist": GestureBinding("hold", ("shift",))})
        adapter = RecordingInput(); controller = GestureController(adapter, profile)
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

    def test_calibration_maps_to_monitor_with_negative_origin(self):
        calibration = MouseCalibration(.1, .9, .1, .9)
        region = ScreenRegion(-1920, 0, 1920, 1080, "left")
        self.assertEqual(calibration.map_to_region(.1, .1, region), (-1920.0, 0.0))
        self.assertEqual(calibration.map_to_region(.9, .9, region), (-1.0, 1079.0))

    def test_calibration_session_captures_four_bounds(self):
        session = CalibrationSession(); session.start()
        self.assertEqual(session.stage, "left")
        self.assertFalse(session.capture(.15, .5))
        self.assertFalse(session.capture(.85, .5))
        self.assertFalse(session.capture(.5, .2))
        self.assertTrue(session.capture(.5, .8))
        self.assertEqual(session.result(), MouseCalibration(.15, .85, .2, .8))

    def test_calibration_session_rejects_reversed_bounds(self):
        session = CalibrationSession(); session.start()
        session.capture(.9, .5); session.capture(.1, .5)
        session.capture(.5, .8); session.capture(.5, .2)
        with self.assertRaises(ValueError): session.result()

    def test_monitor_layout_supports_active_fixed_and_all(self):
        regions = [ScreenRegion(-1920, 0, 1920, 1080, "left"),
                   ScreenRegion(0, 0, 2560, 1440, "main")]
        self.assertEqual(MonitorLayout(regions, "active").target((-100, 500)).name, "left")
        self.assertEqual(MonitorLayout(regions, "fixed", 1).target((-100, 500)).name, "main")
        union = MonitorLayout(regions, "all").target((0, 0))
        self.assertEqual((union.x, union.y, union.width, union.height), (-1920, 0, 4480, 1440))

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

    def test_mouse_uses_active_monitor_and_calibration(self):
        adapter = RecordingInput(); adapter._position = (-100, 500)
        layout = MonitorLayout([ScreenRegion(-1920, 0, 1920, 1080, "left"),
                                ScreenRegion(0, 0, 2560, 1440, "main")], "active")
        controller = MouseController(adapter, self.profile, layout, MouseCalibration(0, 1, 0, 1))
        controller.update(hand((True, False, False, False), "Right"))
        move = next(event for event in adapter.events if event[0] == "move")
        self.assertEqual(controller.target_region.name, "left")
        self.assertLess(move[1], 0)

    def test_two_finger_vertical_motion_scrolls(self):
        adapter = RecordingInput()
        controller = MouseController(adapter, self.profile)
        first = hand((True, True, False, False), "Right")
        points = list(first.landmarks)
        points[8] = (.5, .2, 0); points[12] = (.5, .2, 0)
        second = HandObservation("Right", tuple(points))
        controller.update(first)
        controller.update(second)
        self.assertTrue(any(event[0] == "scroll" for event in adapter.events))
        self.assertEqual(controller.status, "scroll")

    def test_fist_hold_toggles_arming_only_after_release(self):
        controller = ArmingController(ArmingSettings())
        self.assertFalse(controller.armed)
        controller.update("fist", True, 0.0)
        controller.update("fist", True, .5)
        self.assertAlmostEqual(controller.progress, .5)
        self.assertEqual(controller.update("fist", True, 1.01), "armed")
        self.assertTrue(controller.armed)
        self.assertIsNone(controller.update("fist", True, 2.0))
        self.assertTrue(controller.armed)
        for index in range(4):
            controller.update("open_palm", True, 2.1 + index * .05)
        controller.update("fist", True, 2.5)
        self.assertEqual(controller.update("fist", True, 3.51), "disarmed")
        self.assertFalse(controller.armed)

    def test_armed_keyboard_auto_disarms_after_hand_loss(self):
        controller = ArmingController(ArmingSettings(auto_disarm_seconds=2.0))
        controller.update("fist", True, 0.0)
        controller.update("fist", True, 1.01)
        self.assertTrue(controller.armed)
        controller.update("none", False, 2.0)
        self.assertEqual(controller.update("none", False, 4.01), "auto_disarmed")
        self.assertFalse(controller.armed)

    def test_startup_assets_render_at_expected_size(self):
        import cv2
        root = Path(__file__).parents[1]
        screen = StartupScreen(cv2, root / "docs/Splash Screen.png",
                               root / "docs/Loading Screen.png")
        empty = screen.render_loading(0.0, "Starting")
        complete = screen.render_loading(1.0, "Ready")
        self.assertEqual(empty.shape, (626, 1000, 3))
        self.assertEqual(complete.shape, (626, 1000, 3))
        self.assertNotEqual(int(empty.sum()), int(complete.sum()))

    def test_desktop_icon_assets_are_readable(self):
        from PIL import Image
        root = Path(__file__).parents[1]
        for name in ("VisionControl.ico", "VisionControl.icns"):
            with Image.open(root / "assets" / name) as icon:
                self.assertGreaterEqual(icon.width, 256)
                self.assertGreaterEqual(icon.height, 256)

    def test_desktop_settings_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app_settings.json"
            self.assertEqual(load_desktop_settings(path), DesktopSettings())
            expected = DesktopSettings(camera_index=3, start_paused=True)
            save_desktop_settings(path, expected)
            self.assertEqual(load_desktop_settings(path), expected)

    def test_invalid_user_profile_does_not_replace_valid_profile(self):
        root = Path(__file__).parents[1]
        valid = json.loads((root / "config/default_profile.json").read_text())
        invalid = {**valid, "keyboard_hand": valid["mouse_hand"]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "user_profile.json"
            save_user_profile(path, valid)
            original = path.read_text()
            with self.assertRaises(ValueError):
                save_user_profile(path, invalid)
            self.assertEqual(path.read_text(), original)


if __name__ == "__main__": unittest.main()
