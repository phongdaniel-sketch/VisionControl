import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from vision_control.controllers import GestureController, MouseController
from vision_control.profile import GestureBinding, load_profile
from vision_control.types import HandObservation
from vision_control.calibration import CalibrationSession, MouseCalibration
from vision_control.input_adapter import PynputInputAdapter
from vision_control.roles import assign_roles
from vision_control.types import HandsFrame
from vision_control.monitors import EdgeDwellSwitcher, MonitorLayout, ScreenRegion
from vision_control.arming import ArmingController, ArmingSettings
from vision_control.startup import StartupScreen
from vision_control.settings import (DesktopSettings, load_desktop_settings,
                                     save_desktop_settings, save_user_profile,
                                     apply_gesture_bindings, parse_key_list)
from vision_control.paths import user_data_dir


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
        points[tip-3] = (.5 if tip != 20 else .6, .65, 0)
        points[tip-1] = (.5, .4 if up else .6, 0)
    points[0] = (.5, .9, 0); points[9] = (.5, .7, 0)
    points[2], points[3] = (.55, .65, 0), (.52, .58, 0)
    return HandObservation(label, tuple(points))


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile(Path(__file__).parents[1] / "config/default_profile.json")

    def test_profile_loads_and_has_two_roles(self):
        self.assertNotEqual(self.profile.mouse_hand, self.profile.keyboard_hand)
        self.assertTrue(self.profile.swap_hands)
        self.assertEqual(self.profile.monitor_mode, "fixed")
        self.assertEqual(self.profile.fixed_monitor, 0)
        self.assertEqual(self.profile.thresholds["cursor_smoothing"], .6)
        self.assertEqual(self.profile.thresholds["cursor_deadzone_px"], .5)
        self.assertEqual(self.profile.thresholds["mouse_move_gesture"], "any")
        self.assertEqual(
            self.profile.thresholds["mouse_primary_click_gesture"], "pinch_index")
        self.assertEqual(self.profile.thresholds["mouse_scroll_gesture"], "peace")
        self.assertFalse(self.profile.arming.enabled)
        self.assertNotIn("fist", self.profile.bindings)
        self.assertEqual(self.profile.bindings["point"].keys, ("w",))

    def test_keyboard_press_is_debounced(self):
        adapter = RecordingInput(); controller = GestureController(adapter, self.profile)
        point = hand((True, False, False, False))
        for _ in range(5): controller.update(point)
        self.assertEqual([e for e in adapter.events if e == ("press", "w")], [("press", "w")])

    def test_keyboard_press_combination_is_emitted_as_chord(self):
        profile = replace(self.profile, bindings={**self.profile.bindings,
                                                  "point": GestureBinding("press", ("ctrl", "c"))})
        adapter = RecordingInput(); controller = GestureController(adapter, profile)
        point = hand((True, False, False, False))
        for _ in range(3): controller.update(point)
        self.assertEqual(adapter.events, [
            ("key_down", "ctrl"), ("key_down", "c"),
            ("key_up", "c"), ("key_up", "ctrl"),
        ])

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
        from tests.hand_geometry import pose
        adapter = RecordingInput(); controller = MouseController(adapter, self.profile)
        controller.left_down = True
        controller.update(pose('fist'))
        self.assertIn(("up", "left"), adapter.events)

    def test_invalid_profile_rejected(self):
        raw = {"version": 1, "mouse_hand": "Right", "keyboard_hand": "Right", "left_hand": {}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"; path.write_text(json.dumps(raw))
            with self.assertRaises(ValueError): load_profile(path)

    def test_invalid_pinch_hysteresis_is_rejected(self):
        root = Path(__file__).parents[1]
        raw = json.loads((root / "config/default_profile.json").read_text())
        raw["thresholds"]["pinch_close_ratio"] = .6
        raw["thresholds"]["pinch_open_ratio"] = .5
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad-pinch.json"
            path.write_text(json.dumps(raw))
            with self.assertRaisesRegex(ValueError, "pinch_close_ratio"):
                load_profile(path)

    def test_duplicate_mouse_click_mapping_is_rejected(self):
        root = Path(__file__).parents[1]
        raw = json.loads((root / "config/default_profile.json").read_text())
        raw["thresholds"]["mouse_secondary_click_gesture"] = "pinch_index"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad-mouse-map.json"
            path.write_text(json.dumps(raw))
            with self.assertRaisesRegex(ValueError, "must differ"):
                load_profile(path)

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

    def test_monitor_discovery_places_primary_display_at_fixed_index_zero(self):
        from types import SimpleNamespace
        from vision_control.monitors import discover_monitors

        secondary = SimpleNamespace(
            x=1470, y=0, width=1920, height=1080,
            name="secondary", is_primary=False)
        primary = SimpleNamespace(
            x=0, y=0, width=1470, height=956,
            name="primary", is_primary=True)
        with patch("screeninfo.get_monitors", return_value=[secondary, primary]):
            layout = discover_monitors("fixed", 0)
        self.assertTrue(layout.regions[0].is_primary)
        self.assertEqual(layout.target((2000, 500)).name, "primary")

    def test_edge_dwell_switches_once_and_requires_center_release(self):
        left = ScreenRegion(-1920, 0, 1920, 1080, "left")
        main = ScreenRegion(0, 0, 2560, 1440, "main")
        right = ScreenRegion(2560, -200, 1920, 1080, "right")
        switcher = EdgeDwellSwitcher([right, left, main], edge_zone=.1, dwell_seconds=.8)
        self.assertIsNone(switcher.update(.95, main, 0.0))
        self.assertIsNone(switcher.update(.95, main, .4))
        self.assertEqual(switcher.update(.95, main, .81), right)
        self.assertIsNone(switcher.update(.95, right, 2.0))
        self.assertIsNone(switcher.update(.5, right, 2.1))
        self.assertIsNone(switcher.update(.05, right, 2.2))
        self.assertEqual(switcher.update(.05, right, 3.01), main)

    def test_edge_dwell_does_not_wrap_at_outer_display(self):
        left = ScreenRegion(-1920, 0, 1920, 1080, "left")
        main = ScreenRegion(0, 0, 2560, 1440, "main")
        switcher = EdgeDwellSwitcher([main, left], edge_zone=.1, dwell_seconds=.5)
        switcher.update(.05, left, 0.0)
        self.assertIsNone(switcher.update(.05, left, .51))
        self.assertTrue(switcher.latched)

    def test_edge_dwell_requires_active_point_pose(self):
        left = ScreenRegion(-1920, 0, 1920, 1080, "left")
        main = ScreenRegion(0, 0, 2560, 1440, "main")
        switcher = EdgeDwellSwitcher([left, main], edge_zone=.1, dwell_seconds=.5)
        switcher.update(.95, left, 0.0, active=False)
        self.assertIsNone(switcher.update(.95, left, 1.0, active=True))
        self.assertEqual(switcher.progress, 0.0)

    def test_mouse_edge_dwell_moves_cursor_to_next_display_center(self):
        left = ScreenRegion(-1920, 0, 1920, 1080, "left")
        main = ScreenRegion(0, 0, 2560, 1440, "main")
        layout = MonitorLayout([left, main], "active")
        adapter = RecordingInput(); adapter._position = (-500, 500)
        controller = MouseController(adapter, self.profile, layout)
        observation = hand((True, False, False, False), "Right")
        # Translate the entire hand; shifting only the tip changes its joint angle.
        points = [(x + .4, y, z) for x, y, z in observation.landmarks]
        observation = HandObservation("Right", tuple(points))
        with patch("vision_control.controllers.time.monotonic", side_effect=(0.0, .81)):
            controller.update(observation)
            controller.update(observation)
        self.assertEqual(adapter.events[-1], ("move", 1280.0, 720.0))
        self.assertEqual(controller.target_region.name, "main")
        self.assertEqual(controller.status, "switched_right")

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

    def test_mouse_move_pose_can_be_restricted(self):
        profile = replace(
            self.profile,
            thresholds={**self.profile.thresholds, "mouse_move_gesture": "point"},
        )
        adapter = RecordingInput()
        controller = MouseController(adapter, profile)
        controller.update(hand((True, True, True, True), "Right"))
        self.assertFalse(any(event[0] == "move" for event in adapter.events))
        controller.update(hand((True, False, False, False), "Right"))
        self.assertTrue(any(event[0] == "move" for event in adapter.events))

    def test_mouse_scroll_pose_can_be_remapped(self):
        profile = replace(
            self.profile,
            thresholds={**self.profile.thresholds,
                        "mouse_scroll_gesture": "three_fingers"},
        )
        adapter = RecordingInput()
        controller = MouseController(adapter, profile)
        first = hand((True, True, True, False), "Right")
        points = list(first.landmarks)
        for tip in (8, 12):
            points[tip] = (.5, .25, 0)
        first = HandObservation("Right", tuple(points))
        points = list(first.landmarks)
        for tip in (8, 12):
            points[tip] = (.5, .35, 0)
        second = HandObservation("Right", tuple(points))
        controller.update(first)
        controller.update(second)
        self.assertTrue(any(event[0] == "scroll" for event in adapter.events))

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
        self.assertTrue((screen.render_loading(.52, "First stage") ==
                         screen.render_loading(.52, "Different stage")).all())
        x, center_y, width, _height = screen._bar_geometry()
        warm = complete[center_y, x + 12]
        cool = complete[center_y, x + int(width * .84)]
        self.assertGreater(int(warm[2]), int(warm[0]))
        self.assertGreater(int(cool[0]), int(cool[2]))

    def test_desktop_icon_assets_are_readable(self):
        from PIL import Image
        root = Path(__file__).parents[1]
        for name in ("VisionControl.ico", "VisionControl.icns"):
            with Image.open(root / "assets" / name) as icon:
                self.assertGreaterEqual(icon.width, 256)
                self.assertGreaterEqual(icon.height, 256)

    def test_bundled_hand_model_is_present(self):
        model = Path(__file__).parents[1] / "assets/models/hand_landmarker.task"
        self.assertGreater(model.stat().st_size, 1_000_000)

    def test_desktop_settings_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app_settings.json"
            self.assertEqual(load_desktop_settings(path), DesktopSettings())
            expected = DesktopSettings(camera_index=3, start_paused=True)
            save_desktop_settings(path, expected)
            self.assertEqual(load_desktop_settings(path), expected)

    def test_user_data_directory_is_platform_specific(self):
        home = Path("/Users/example")
        self.assertEqual(user_data_dir("darwin", {}, home),
                         home / "Library/Application Support/VisionControl")
        self.assertEqual(user_data_dir("win32", {"LOCALAPPDATA": "C:/Local"}, home),
                         Path("C:/Local/VisionControl"))
        self.assertEqual(user_data_dir("linux", {"XDG_CONFIG_HOME": "/tmp/config"}, home),
                         Path("/tmp/config/visioncontrol"))

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

    def test_gesture_key_list_accepts_supported_combinations(self):
        self.assertEqual(parse_key_list("Ctrl + C"), ("ctrl", "c"))
        self.assertEqual(parse_key_list("shift, left"), ("shift", "left"))
        with self.assertRaisesRegex(ValueError, "Unsupported key"):
            parse_key_list("volume_up")

    def test_gesture_bindings_can_be_changed_or_disabled(self):
        root = Path(__file__).parents[1]
        raw = json.loads((root / "config/default_profile.json").read_text())
        updated = apply_gesture_bindings(raw, {
            "point": ("Hold", "ctrl, c"),
            "peace": ("Disabled", ""),
        })
        self.assertEqual(updated["left_hand"]["point"],
                         {"type": "hold", "keys": ["ctrl", "c"]})
        self.assertNotIn("peace", updated["left_hand"])
        self.assertIn("peace", raw["left_hand"])

    def test_fist_cannot_be_configured_in_gesture_editor(self):
        root = Path(__file__).parents[1]
        raw = json.loads((root / "config/default_profile.json").read_text())
        with self.assertRaisesRegex(ValueError, "cannot be configured"):
            apply_gesture_bindings(raw, {"fist": ("Press", "space")})

    def test_runtime_pause_releases_all_control_state(self):
        from vision_control.runtime import VisionRuntime

        class Releasable:
            def __init__(self): self.calls = 0
            def release_all(self): self.calls += 1

        class Arming:
            def __init__(self): self.calls = 0
            def disarm(self): self.calls += 1

        runtime = VisionRuntime(start_paused=False)
        runtime.mouse = Releasable()
        runtime.keyboard = Releasable()
        runtime.arming = Arming()
        runtime.set_paused(True)
        self.assertTrue(runtime.paused)
        self.assertEqual(runtime.mouse.calls, 1)
        self.assertEqual(runtime.keyboard.calls, 1)
        self.assertEqual(runtime.arming.calls, 1)

    def test_runtime_close_is_idempotent_when_partial_cleanup_fails(self):
        from vision_control.runtime import VisionRuntime

        class FailingClose:
            def __init__(self): self.calls = 0
            def close(self):
                self.calls += 1
                raise ValueError("already closed")

        class Adapter:
            def __init__(self): self.calls = 0
            def release_all(self): self.calls += 1

        runtime = VisionRuntime()
        tracker = FailingClose()
        adapter = Adapter()
        runtime.tracker = tracker
        runtime.adapter = adapter
        runtime.close()
        runtime.close()
        self.assertEqual(tracker.calls, 1)
        self.assertEqual(adapter.calls, 1)
        self.assertIsNone(runtime.tracker)
        self.assertIsNone(runtime.adapter)

    def test_controller_opens_settings_only_from_button_and_disables_voice(self):
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        from vision_control.controller_ui import ControllerWindow
        import vision_control.settings_ui as settings_ui

        class FakeRuntime:
            def __init__(self, profile):
                self.profile = profile
                self.paused = False
                self.pause_calls = 0
                self.close_calls = 0
                self.started = True

            def set_paused(self, value):
                self.paused = value
                self.pause_calls += 1

            def toggle_paused(self):
                self.set_paused(not self.paused)
                return self.paused

            def close(self): self.close_calls += 1

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            app_settings = Path(directory) / "app_settings.json"
            user_profile = Path(directory) / "user_profile.json"
            with patch.object(settings_ui, "APP_SETTINGS", app_settings), \
                 patch.object(settings_ui, "USER_PROFILE", user_profile):
                runtime = FakeRuntime(self.profile)
                window = ControllerWindow(runtime)
                window.timer.stop()
                self.assertIsNone(window.settings_window)
                self.assertFalse(window.voice_button.isEnabled())
                window.settings_button.click()
                app.processEvents()
                self.assertIsNotNone(window.settings_window)
                self.assertFalse(window.timer.isActive())
                self.assertFalse(window.settings_window.voice_button.isEnabled())
                self.assertEqual(window.settings_window.camera.value(), DesktopSettings().camera_index)
                self.assertEqual(
                    window.settings_window.monitor_mode.currentText(), "fixed")
                self.assertEqual(window.settings_window.fixed_monitor.currentData(), 0)
                self.assertIn("Primary", window.settings_window.fixed_monitor.currentText())
                self.assertIn("×", window.settings_window.fixed_monitor.currentText())
                self.assertIn('Gestures', window.settings_window.nav_buttons)
                self.assertNotIn('Gesture v1', window.settings_window.nav_buttons)
                self.assertNotIn('enabled', window.settings_window.v1_panel.controls)
                self.assertTrue(runtime.paused)
                self.assertGreaterEqual(runtime.pause_calls, 1)
                window.settings_window.close()
                app.processEvents()
                self.assertTrue(window.timer.isActive())
                window.close()
                app.processEvents()

    def test_controller_frame_error_releases_runtime_without_closing_window(self):
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication, QMessageBox
        from vision_control.controller_ui import ControllerWindow

        class FailingRuntime:
            def __init__(self, profile):
                self.profile = profile
                self.paused = False
                self.pause_calls = 0
                self.close_calls = 0

            def process_frame(self):
                raise RuntimeError("camera frame unavailable")

            def set_paused(self, value):
                self.paused = value
                self.pause_calls += 1

            def toggle_paused(self):
                return self.paused

            def close(self):
                self.close_calls += 1

        app = QApplication.instance() or QApplication([])
        runtime = FailingRuntime(self.profile)
        window = ControllerWindow(runtime)
        window.timer.stop()
        window.show()
        with patch.object(QMessageBox, "critical", return_value=None):
            window._process_frame()
        app.processEvents()
        self.assertTrue(window.isVisible())
        self.assertEqual(window.frame_error, "camera frame unavailable")
        self.assertTrue(runtime.paused)
        self.assertEqual(runtime.pause_calls, 1)
        self.assertEqual(runtime.close_calls, 1)
        self.assertFalse(window.pause_button.isEnabled())
        window.close()
        app.processEvents()

    def test_settings_tooltips_and_gesture_advanced_values_round_trip(self):
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        import vision_control.settings_ui as settings_ui

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            app_settings = Path(directory) / "app_settings.json"
            user_profile = Path(directory) / "user_profile.json"
            with patch.object(settings_ui, "APP_SETTINGS", app_settings), \
                 patch.object(settings_ui, "USER_PROFILE", user_profile):
                window = settings_ui.SettingsWindow("Gestures")
                explained = [
                    window.camera, window.start_paused, window.mouse_hand,
                    window.swap_hands, window.monitor_mode, window.fixed_monitor,
                    window.smoothing, window.deadzone, window.scroll,
                    window.edge_switch, window.edge_dwell, window.edge_zone,
                    window.arm_hold, window.arm_release_frames,
                    window.arm_cooldown, window.auto_disarm,
                    window.gesture_confidence, window.gesture_on_frames,
                    window.pinch_close, window.pinch_open, window.drag_hold,
                    window.scroll_deadzone,
                    window.mouse_move_gesture, window.mouse_primary_click,
                    window.mouse_secondary_click, window.mouse_scroll_gesture,
                ]
                explained.extend(window.nav_buttons.values())
                for action, keys in window.gesture_rows.values():
                    explained.extend((action, keys))
                self.assertTrue(all(control.toolTip().strip()
                                    for control in explained))
                self.assertNotIn("fist", window.gesture_rows)

                action, keys = window.gesture_rows["peace"]
                action.setCurrentText("Hold")
                keys.setText("ctrl, c")
                window.arm_hold.setValue(1.4)
                window.auto_disarm.setValue(3.5)
                window.gesture_confidence.setValue(.8)
                window.gesture_on_frames.setValue(2)
                window.pinch_close.setValue(.3)
                window.pinch_open.setValue(.55)
                window.drag_hold.setValue(.6)
                window.scroll_deadzone.setValue(.02)
                window.pinch_confirm.setValue(.12)
                window.adaptive_smoothing.setChecked(True)
                window._set_combo_data(window.mouse_move_gesture, "point")
                window._set_combo_data(window.mouse_primary_click, "pinch_middle")
                window._set_combo_data(window.mouse_secondary_click, "disabled")
                window._set_combo_data(window.mouse_scroll_gesture, "open_palm")
                self.assertTrue(window.save())
                app.processEvents()

                profile = load_profile(user_profile)
                self.assertEqual(profile.bindings["peace"].action_type, "hold")
                self.assertEqual(profile.bindings["peace"].keys, ("ctrl", "c"))
                self.assertEqual(profile.arming.hold_seconds, 1.4)
                self.assertEqual(profile.arming.auto_disarm_seconds, 3.5)
                self.assertEqual(profile.thresholds["gesture_confidence"], .8)
                self.assertEqual(profile.thresholds["gesture_on_frames"], 2)
                self.assertEqual(profile.thresholds["pinch_close_ratio"], .3)
                self.assertEqual(profile.thresholds["pinch_open_ratio"], .55)
                self.assertEqual(profile.thresholds["drag_hold_seconds"], .6)
                self.assertEqual(profile.thresholds["scroll_deadzone"], .02)
                self.assertEqual(profile.thresholds["pinch_confirm_seconds"], .12)
                self.assertTrue(profile.thresholds["cursor_adaptive_smoothing"])
                self.assertEqual(profile.thresholds["mouse_move_gesture"], "point")
                self.assertEqual(
                    profile.thresholds["mouse_primary_click_gesture"], "pinch_middle")
                self.assertEqual(
                    profile.thresholds["mouse_secondary_click_gesture"], "disabled")
                self.assertEqual(
                    profile.thresholds["mouse_scroll_gesture"], "open_palm")


if __name__ == "__main__": unittest.main()
