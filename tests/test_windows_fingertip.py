import json
import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tests.test_core import RecordingInput, hand
from vision_control.controllers import GestureController, MouseController
from vision_control.input_adapter import PynputInputAdapter
from vision_control.profile import GestureBinding, load_profile
from vision_control.runtime import VisionRuntime


ROOT = Path(__file__).parents[1]


class WindowsFingertipTests(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile(ROOT / 'config/default_profile.json')

    def adapter(self):
        adapter = object.__new__(PynputInputAdapter)
        adapter.keyboard = Mock()
        adapter.mouse = Mock()
        adapter.keys = {}
        adapter.buttons = {'left': 'left', 'right': 'right'}
        adapter.held_keys = set()
        adapter.held_buttons = set()
        return adapter

    def test_failed_single_press_release_is_retried(self):
        adapter = self.adapter()
        adapter.keyboard.release.side_effect = [OSError('release failed'), None]
        with self.assertRaises(OSError):
            adapter.key_press('a')
        self.assertEqual(adapter.held_keys, {'a'})
        adapter.release_all()
        self.assertFalse(adapter.held_keys)
        self.assertEqual(adapter.keyboard.release.call_count, 2)

    def test_failed_release_does_not_skip_other_inputs(self):
        adapter = self.adapter()
        adapter.key_down('a')
        adapter.key_down('b')
        adapter.button_down('left')
        adapter.button_down('right')
        adapter.keyboard.release.side_effect = lambda key: (
            (_ for _ in ()).throw(OSError('a failed')) if key == 'a' else None)
        with self.assertRaises(ExceptionGroup):
            adapter.release_all()
        self.assertEqual(adapter.held_keys, {'a'})
        self.assertFalse(adapter.held_buttons)
        self.assertEqual(adapter.mouse.release.call_count, 2)
        adapter.keyboard.release.side_effect = None
        adapter.release_all()
        self.assertFalse(adapter.held_keys)

    def test_mouse_release_attempts_both_buttons_and_keeps_failed_state(self):
        adapter = self.adapter()
        controller = MouseController(adapter, self.profile)
        controller.left_down = controller.right_down = True
        adapter.mouse.release.side_effect = [OSError('left failed'), None]
        with self.assertRaises(ExceptionGroup):
            controller.release_all()
        self.assertTrue(controller.left_down)
        self.assertFalse(controller.right_down)
        adapter.mouse.release.side_effect = None
        controller.release_all()
        self.assertFalse(controller.left_down)

    def test_chord_release_failure_still_releases_modifier(self):
        adapter = self.adapter()
        adapter.keyboard.release.side_effect = lambda key: (
            (_ for _ in ()).throw(OSError('c failed')) if key == 'c' else None)
        profile = replace(self.profile, bindings={'point': GestureBinding('press', ('ctrl', 'c'))},
                          thresholds={**self.profile.thresholds, 'gesture_on_frames': 1})
        controller = GestureController(adapter, profile)
        with self.assertRaises(ExceptionGroup):
            controller.update(hand((True, False, False, False)))
        self.assertEqual(adapter.held_keys, {'c'})
        adapter.keyboard.release.assert_any_call('ctrl')

    def test_runtime_close_retains_failed_adapter_for_retry(self):
        runtime = VisionRuntime()
        adapter = self.adapter()
        adapter.key_down('a')
        adapter.keyboard.release.side_effect = OSError('failed')
        runtime.adapter = adapter
        runtime.close()
        self.assertIs(runtime.adapter, adapter)
        adapter.keyboard.release.side_effect = None
        runtime.close()
        self.assertIsNone(runtime.adapter)
        self.assertFalse(adapter.held_keys)

    def test_calibration_rejects_missing_or_ambiguous_swapped_mouse_hand(self):
        runtime = VisionRuntime()
        runtime.profile = replace(self.profile, swap_hands=True)
        runtime.start_calibration()
        for hands in [(hand(label='Right'),), (hand(label='Left'), hand(label='Left'))]:
            runtime.last_snapshot = SimpleNamespace(hands=hands)
            self.assertFalse(runtime.capture_calibration())
            self.assertEqual(runtime.calibration_session.stage, 'left')
        runtime.last_snapshot = SimpleNamespace(hands=(hand(label='Left'),))
        runtime.capture_calibration()
        self.assertEqual(runtime.calibration_session.stage, 'right')

    def test_pointer_mode_validation_and_legacy_default(self):
        raw = json.loads((ROOT / 'config/default_profile.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'profile.json'
            raw.pop('pointer_mode')
            path.write_text(json.dumps(raw))
            self.assertEqual(load_profile(path).pointer_mode, 'gesture')
            raw['pointer_mode'] = 'unknown'
            path.write_text(json.dumps(raw))
            with self.assertRaisesRegex(ValueError, 'pointer_mode'):
                load_profile(path)

    def test_camera_defaults_are_platform_specific_and_saved_index_wins(self):
        from vision_control.settings import DesktopSettings, load_desktop_settings
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.json'
            for platform, expected in [('win32', 0), ('darwin', 1)]:
                with patch('vision_control.settings.sys.platform', platform):
                    self.assertEqual(DesktopSettings().camera_index, expected)
                    path.write_text('{"camera_index": 3}')
                    self.assertEqual(load_desktop_settings(path).camera_index, 3)

    def test_camera_backend_and_cleanup_on_each_platform(self):
        import cv2
        from vision_control.camera import Camera
        for platform in ('win32', 'darwin'):
            with patch('vision_control.camera.sys.platform', platform), patch.object(
                    cv2, 'VideoCapture') as capture:
                camera = Camera(index=2)
                camera.open()
                capture.assert_called_once_with(*((2, cv2.CAP_DSHOW)
                                                 if platform == 'win32' else (2,)))
                camera.close()
                camera.close()
                capture.return_value.release.assert_called_once()

    def test_fingertip_gates_movement_and_preserves_custom_mapping(self):
        profile = replace(self.profile, pointer_mode='index_fingertip', thresholds={
            **self.profile.thresholds, 'mouse_move_gesture': 'three_fingers'})
        adapter = RecordingInput()
        controller = MouseController(adapter, profile)
        controller.update(hand((True, True, True, False)))
        self.assertFalse(any(e[0] == 'move' for e in adapter.events))
        controller.update(hand((True, False, False, False)))
        self.assertTrue(any(e[0] == 'move' for e in adapter.events))
        self.assertEqual(profile.thresholds['mouse_move_gesture'], 'three_fingers')
        controller.left_down = True
        controller.update(None)
        self.assertIn(('up', 'left'), adapter.events)
        self.assertFalse(controller.left_down)

    def test_fingertip_pinch_drag_and_fist_release(self):
        from tests.hand_geometry import pose
        profile = replace(self.profile, pointer_mode='index_fingertip')
        adapter = RecordingInput()
        controller = MouseController(adapter, profile)
        pinching = pose('pinch')
        with patch('vision_control.controllers.time.monotonic', side_effect=[.9, 1.0, 1.1]):
            controller.update(pose('point'))
            controller.update(pinching)
            self.assertNotIn(('down', 'left'), adapter.events)
            controller.update(pinching)
        self.assertIn(('down', 'left'), adapter.events)
        self.assertTrue(any(e[0] == 'move' for e in adapter.events))
        controller.update(pose('fist'))
        self.assertIn(('up', 'left'), adapter.events)
        self.assertFalse(controller.left_down)

    def test_fingertip_scroll_does_not_move_cursor(self):
        profile = replace(self.profile, pointer_mode='index_fingertip')
        adapter = RecordingInput()
        controller = MouseController(adapter, profile)
        peace = hand((True, True, False, False))
        controller.update(peace)
        points = list(peace.landmarks)
        for index in (8, 12):
            x, y, z = points[index]
            points[index] = (x, y + .05, z)
        controller.update(replace(peace, landmarks=tuple(points)))
        self.assertTrue(any(event[0] == 'scroll' for event in adapter.events))
        self.assertFalse(any(event[0] == 'move' for event in adapter.events))

    def test_fingertip_marker_is_drawn_at_index_tip(self):
        import cv2
        import numpy as np
        from vision_control.overlay import Overlay
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        Overlay(cv2).draw_fingertip(frame, hand((True, False, False, False)))
        self.assertGreater(int(frame[144, 320].sum()), 0)
        self.assertEqual(int(frame[0, 0].sum()), 0)

    def test_settings_mode_round_trip_and_restore_mapping(self):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PySide6.QtWidgets import QApplication
        import vision_control.settings_ui as ui
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            profile_path = Path(directory) / 'profile.json'
            with patch.object(ui, 'USER_PROFILE', profile_path), patch.object(
                    ui, 'APP_SETTINGS', Path(directory) / 'settings.json'):
                window = ui.SettingsWindow('Mouse')
                window._set_combo_data(window.mouse_move_gesture, 'three_fingers')
                self.assertEqual(window.pointer_mode.count(), 2)
                window._set_combo_data(window.pointer_mode, 'thumb_lock')
                self.assertTrue(window.save())
                app.processEvents()
                self.assertEqual(load_profile(profile_path).pointer_mode, 'thumb_lock')
                window = ui.SettingsWindow('Mouse')
                self.assertEqual(window.pointer_mode.currentData(), 'thumb_lock')
                window._set_combo_data(window.pointer_mode, 'palm')
                self.assertEqual(window.mouse_move_gesture.currentData(), 'three_fingers')
                self.assertTrue(window.save())
                app.processEvents()
                self.assertEqual(load_profile(profile_path).pointer_mode, 'palm')

    def test_settings_camera_retry_failure_stays_open(self):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PySide6.QtWidgets import QApplication, QMessageBox
        from vision_control.controller_ui import ControllerWindow
        app = QApplication.instance() or QApplication([])
        runtime = VisionRuntime(start_paused=True)
        runtime.profile = self.profile
        failed = VisionRuntime(start_paused=True)
        failed.profile = self.profile
        failed.start = Mock(side_effect=RuntimeError('camera unavailable'))
        window = ControllerWindow(runtime, runtime_factory=Mock(return_value=failed))
        window.timer.stop()
        window.show()
        with patch.object(QMessageBox, 'critical'):
            window._reload_after_settings()
        self.assertTrue(window.isVisible())
        self.assertFalse(window.timer.isActive())
        self.assertFalse(window.pause_button.isEnabled())
        self.assertEqual(window.status_mode.text(), 'ERROR · PAUSED')
        window.close()
        app.processEvents()
