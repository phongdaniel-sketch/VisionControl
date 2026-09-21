import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tests.test_core import hand
from vision_control.calibration import MouseCalibration, load_calibration, save_calibration
from vision_control.controller_labels import display_name, mouse_guide
from vision_control.profile import load_profile
from vision_control.runtime import RuntimeSnapshot, VisionRuntime


class ControllerClarityTests(unittest.TestCase):
    def setUp(self):
        self.runtime = VisionRuntime()
        self.runtime.profile = load_profile(Path(__file__).parents[1] / 'config/default_profile.json')
        self.runtime.mouse = SimpleNamespace(calibration=MouseCalibration(), release_all=Mock())
        self.runtime.started = True
        self.snapshot_at(.2, .4)

    def snapshot_at(self, x, y, found=True):
        observation = hand((True, False, False, False), 'Left')
        points = list(observation.landmarks)
        points[8] = (x, y, 0)
        observation = replace(observation, landmarks=tuple(points))
        snapshot = RuntimeSnapshot(None, True, 'Right', 'Left', 'paused',
            (observation,) if found else (), found, False, 'paused', r'\\.\DISPLAY2',
            'DISARMED', 0, mouse_pose='point' if found else 'none')
        self.runtime.last_snapshot = snapshot
        return snapshot

    def window(self):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PySide6.QtWidgets import QApplication
        from vision_control.controller_ui import ControllerWindow
        self.app = QApplication.instance() or QApplication([])
        window = ControllerWindow(self.runtime)
        window.timer.stop()
        self.addCleanup(window.close)
        return window

    def test_display_prefix_removed_without_changing_custom_names(self):
        self.assertEqual(display_name(r'\\.\DISPLAY2'), 'Display 2')
        self.assertEqual(display_name('DELL U2424HE'), 'DELL U2424HE')

    def test_space_toggles_pause_and_is_blocked_during_settings(self):
        window = self.window()
        before = self.runtime.paused
        window.space_action()
        self.assertNotEqual(self.runtime.paused, before)
        window.space_action()
        self.assertEqual(self.runtime.paused, before)
        window.settings_window = Mock()
        window.space_action()
        self.assertEqual(self.runtime.paused, before)
        window.settings_window = None

    def test_diagnostics_closes_camera_before_open_and_restores_paused(self):
        window = self.window()
        calls = []
        self.runtime.close = Mock(side_effect=lambda: calls.append('close'))
        self.runtime.start = Mock(side_effect=lambda: calls.append('restore'))
        with patch('vision_control.diagnostics_ui.DiagnosticWindow') as factory:
            factory.side_effect = lambda runtime: calls.append('debug') or Mock()
            window.open_diagnostics()
        self.assertEqual(calls, ['close', 'debug'])
        self.assertTrue(self.runtime.paused)
        self.assertFalse(window.timer.isActive())
        window._diagnostics_closed()
        self.assertEqual(calls[-1], 'restore')
        self.assertTrue(self.runtime.paused)
        self.assertTrue(window.timer.isActive())
        window.timer.stop()

    def test_calibration_overlay_draws_saved_bounds(self):
        import cv2
        import numpy as np
        from vision_control.overlay import Overlay
        source = np.zeros((101, 201, 3), dtype=np.uint8)
        result = Overlay(cv2).draw_calibration(source.copy(), MouseCalibration(.2,.8,.3,.9))
        self.assertTrue(result[30,40].any())
        self.assertTrue(result[90,160].any())
        self.assertTrue(result[60,100].any())
        self.assertFalse(source.any())

    def test_mouse_guide_tracks_disabled_swapped_click_mapping(self):
        profile = replace(self.runtime.profile, pointer_mode='index_fingertip', thresholds={
            **self.runtime.profile.thresholds, 'mouse_primary_click_gesture': 'pinch_middle',
            'mouse_secondary_click_gesture': 'disabled'})
        entries = dict(mouse_guide(profile))
        self.assertIn('index', entries['Move pointer'])
        self.assertIn('middle', entries['Left click / drag'])
        self.assertEqual(entries['Right click / drag'], 'Disabled')

    def test_palm_guide_describes_curl_clicks_and_palm_movement(self):
        profile = replace(self.runtime.profile, pointer_mode='palm')
        entries = dict(mouse_guide(profile))
        self.assertIn('palm center', entries['Move pointer'])
        self.assertIn('Index + middle', entries['Middle click'])
        self.assertIn('curl', entries['Middle click'])
        self.assertIn('Thumb + middle', entries['Right click'])
        self.assertIn('touch = click', entries['Right click'])

    def test_paused_status_still_shows_pose_and_role_aware_guide(self):
        from PySide6.QtWidgets import QLabel
        window = self.window()
        window._render_status(self.runtime.last_snapshot)
        self.assertEqual(window.status_gesture.text(), 'Point')
        self.assertEqual(window.status_action.text(), 'Input paused')
        self.assertEqual(window.status_monitor.text(), 'Display 2')
        self.assertIn('Mouse hand', window.guide_selector.currentText())
        window.guide_selector.setCurrentIndex(1)
        texts = [label.text() for label in window.findChildren(QLabel)]
        self.assertTrue(any('Press once: W' in text for text in texts))
        self.assertIn('ACTIVE', window.guide_note.text())
        self.assertNotIn('ARMED', window.guide_note.text())

    def test_calibration_saves_four_bounds_and_stays_paused(self):
        window = self.window()
        with tempfile.TemporaryDirectory() as directory, patch(
                'vision_control.runtime.runtime_data_dir', return_value=Path(directory)):
            window.start_calibration()
            self.assertTrue(self.runtime.paused)
            for x, y in [(.2, .4), (.8, .4), (.5, .2), (.5, .8)]:
                self.snapshot_at(x, y)
                window.capture_calibration()
            self.assertFalse(self.runtime.calibration_session.active)
            self.assertTrue(self.runtime.paused)
            self.assertIn('saved locally', window.help_label.text())
            self.assertEqual(load_calibration(Path(directory) / 'mouse_calibration.json'),
                             MouseCalibration(.2, .8, .2, .8))

    def test_invalid_boundary_stays_on_step_and_cancel_keeps_old_mapping(self):
        window = self.window()
        old = self.runtime.mouse.calibration
        window.start_calibration()
        window.capture_calibration()
        self.snapshot_at(.1, .4)
        window.capture_calibration()
        self.assertEqual(self.runtime.calibration_session.stage, 'right')
        self.assertIn('farther RIGHT', window.help_label.text())
        window.cancel_calibration()
        self.assertIs(self.runtime.mouse.calibration, old)
        self.assertTrue(self.runtime.paused)

    def test_lost_hand_cancels_countdown_without_capturing(self):
        window = self.window()
        window.start_calibration()
        window.schedule_capture()
        self.assertIsNotNone(window.capture_deadline)
        window._update_calibration(self.snapshot_at(.2, .4, False))
        self.assertIsNone(window.capture_deadline)
        self.assertEqual(self.runtime.calibration_session.stage, 'left')
        self.assertFalse(window.capture_button.isEnabled())

    def test_countdown_records_current_boundary(self):
        window = self.window()
        window.start_calibration()
        window.capture_deadline = 0
        window._update_calibration(self.runtime.last_snapshot)
        self.assertEqual(self.runtime.calibration_session.stage, 'right')
        self.assertIsNone(window.capture_deadline)

    def test_atomic_save_failure_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'calibration.json'
            save_calibration(path, MouseCalibration())
            original = path.read_bytes()
            with patch('vision_control.calibration.os.replace', side_effect=OSError('cannot save')):
                with self.assertRaises(OSError):
                    save_calibration(path, MouseCalibration(.2, .8, .2, .8))
            self.assertEqual(path.read_bytes(), original)

    def test_space_captures_when_countdown_button_has_focus(self):
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        window = self.window()
        window.show()
        window.activateWindow()
        self.app.processEvents()
        window.start_calibration()
        window.capture_button.setFocus()
        self.app.processEvents()
        QTest.keyClick(window.capture_button, Qt.Key.Key_Space)
        self.app.processEvents()
        self.assertEqual(self.runtime.calibration_session.stage, 'right')
