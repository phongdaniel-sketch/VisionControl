import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from vision_control.controller_ui import ControllerWindow
from vision_control.profile import load_profile
from vision_control.runtime import VisionRuntime
from vision_control.calibration import MouseCalibration


class SystemTrayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.runtime = VisionRuntime()
        self.runtime.profile = load_profile(Path(__file__).parents[1] / 'config/default_profile.json')
        self.runtime.mouse = SimpleNamespace(calibration=MouseCalibration(), release_all=Mock())
        self.runtime.started = True
        self.runtime.set_paused(True)
        self.window = ControllerWindow(self.runtime, enable_tray=True)
        self.window.timer.stop()
        self.addCleanup(self.window.shutdown)
        self.addCleanup(self.window.hide)

    def test_escape_hides_and_reopen_keeps_runtime(self):
        self.window.show()
        self.runtime.set_paused(False)
        with patch.object(self.window.tray, 'available', return_value=True):
            self.window.hide_to_tray()
            self.assertFalse(self.window.isVisible())
            self.assertFalse(self.window.closing)
            self.assertFalse(self.runtime.paused)
            self.assertTrue(self.runtime.started)
            self.window.show_controller()
            self.assertTrue(self.window.isVisible())

    def test_escape_key_routes_to_tray_without_shutdown(self):
        self.window.show()
        with patch.object(self.window.tray, 'available', return_value=True):
            event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape,
                              Qt.KeyboardModifier.NoModifier)
            self.window.keyPressEvent(event)
        self.assertFalse(self.window.isVisible())
        self.assertTrue(self.window.hidden_in_tray)
        self.assertFalse(self.window.closing)
        self.assertTrue(self.runtime.started)

    def test_close_always_exits_and_releases(self):
        self.window.close()
        self.assertTrue(self.window.closing)
        self.assertFalse(self.runtime.started)
        self.runtime.mouse.release_all.assert_called()
        self.assertFalse(self.window.tray.icon.isVisible())

    def test_escape_minimizes_when_tray_is_unavailable(self):
        self.window.show()
        with patch.object(self.window.tray, 'available', return_value=False):
            self.window.hide_to_tray()
        self.assertTrue(self.window.isMinimized())
        self.assertFalse(self.window.closing)

    def test_start_pause_and_release(self):
        self.assertEqual(self.window.pause_button.text(), 'Start')
        self.window.tray.toggle_action.trigger()
        self.assertFalse(self.runtime.paused)
        self.assertEqual(self.window.tray.state, 'Active')
        self.window.tray.toggle_action.trigger()
        self.assertTrue(self.runtime.paused)
        self.runtime.mouse.release_all.assert_called()
        self.assertEqual(self.window.tray.toggle_action.text(), 'Start')

    def test_start_blocked_by_each_exclusive_state(self):
        for attribute, value in [('settings_window', Mock()), ('diagnostic_window', Mock()),
                                 ('frame_error', 'camera error')]:
            with self.subTest(attribute=attribute):
                setattr(self.window, attribute, value)
                self.window.tray.refresh()
                self.assertFalse(self.window.tray.toggle_action.isEnabled())
                self.window.toggle_pause()
                self.assertTrue(self.runtime.paused)
                setattr(self.window, attribute, None)
        self.runtime.start_calibration()
        self.window.tray.refresh()
        self.assertFalse(self.window.tray.toggle_action.isEnabled())
        self.window.toggle_pause()
        self.assertTrue(self.runtime.paused)

    def test_hidden_error_restores_controller(self):
        self.window.hide()
        with patch('vision_control.controller_ui.QMessageBox.critical'):
            self.window.show_runtime_error(RuntimeError('camera lost'))
        self.assertTrue(self.window.isVisible())
        self.assertEqual(self.window.tray.state, 'Error')
        self.assertFalse(self.window.tray.toggle_action.isEnabled())
        self.runtime.mouse.release_all.assert_called()

    def test_shutdown_attempts_all_cleanup_and_is_idempotent(self):
        self.window.diagnostic_window = Mock()
        self.window.diagnostic_window.close.side_effect = RuntimeError('child failed')
        self.window.settings_window = Mock()
        self.runtime.close = Mock(wraps=self.runtime.close)
        self.window.shutdown()
        self.window.shutdown()
        self.runtime.close.assert_called_once()
        self.window.settings_window.close.assert_called_once()
        self.assertFalse(self.window.tray.icon.isVisible())
        self.assertFalse(self.window.timer.isActive())

    def test_hidden_processing_continues(self):
        self.window.hide()
        self.runtime.process_frame = Mock(return_value=None)
        self.runtime.cursor_tick = Mock()
        self.window._process_frame()
        self.runtime.process_frame.assert_called_once()
        self.runtime.cursor_tick.assert_called_once()

    def test_hidden_paused_stops_workers_and_wakes_on_start(self):
        worker = Mock()
        self.runtime.perception = worker
        self.runtime.last_snapshot = object()
        self.window.hidden_in_tray = True
        self.window._suspend_if_idle()
        worker.close.assert_called_once()
        self.assertIsNone(self.runtime.perception)
        self.assertIsNone(self.runtime.last_snapshot)
        self.assertTrue(self.window.perception_suspended)
        self.assertFalse(self.window.timer.isActive())
        self.runtime.async_mode = True
        with patch('vision_control.perception_worker.LatestPerception') as factory:
            self.window.toggle_pause()
            factory.return_value.start.assert_called_once()
        self.assertFalse(self.runtime.paused)
        self.assertFalse(self.window.perception_suspended)
        self.assertTrue(self.window.timer.isActive())

    def test_open_wakes_preview_without_starting_input(self):
        self.window.hidden_in_tray = True
        self.window._suspend_if_idle()
        self.runtime.wake_perception = Mock()
        self.window.show_controller()
        self.runtime.wake_perception.assert_called_once()
        self.assertTrue(self.runtime.paused)
        self.assertTrue(self.runtime.preview_enabled)
        self.assertFalse(self.window.hidden_in_tray)

    def test_failed_wake_stays_paused_and_shows_error(self):
        self.window.hidden_in_tray = True
        self.window._suspend_if_idle()
        self.runtime.wake_perception = Mock(side_effect=RuntimeError('wake failed'))
        with patch('vision_control.controller_ui.QMessageBox.critical'):
            self.window.toggle_pause()
        self.assertTrue(self.runtime.paused)
        self.assertEqual(self.window.frame_error, 'wake failed')
        self.assertFalse(self.window.timer.isActive())
        self.assertTrue(self.window.isVisible())

    def test_hidden_active_skips_widget_and_preview_work(self):
        self.window.hidden_in_tray = True
        self.runtime.set_paused(False)
        self.runtime.process_frame = Mock(return_value=SimpleNamespace(frame=None))
        self.runtime.cursor_tick = Mock()
        self.window._render_frame = Mock()
        self.window._render_status = Mock()
        self.window._process_frame()
        self.runtime.cursor_tick.assert_called_once()
        self.window._render_frame.assert_not_called()
        self.window._render_status.assert_not_called()
        self.window._suspend_if_idle()
        self.assertFalse(self.window.perception_suspended)

    def test_background_runtime_skips_overlays_and_debug_logs(self):
        import time
        import numpy as np
        from vision_control.types import HandsFrame
        self.runtime.preview_enabled = False
        self.runtime.debug_enabled = True
        self.runtime.landmarks_enabled = True
        self.runtime.overlay = Mock()
        self.runtime.mouse.status = 'paused'
        self.runtime.mouse.target_region = SimpleNamespace(name='Display')
        self.runtime.arming = SimpleNamespace(label='Paused', progress=0., disarm=Mock())
        self.runtime.perception = Mock()
        stamp = time.monotonic()
        self.runtime.perception.take.return_value = (
            1, np.zeros((4,4,3), dtype=np.uint8), HandsFrame(stamp, (), 4, 4), stamp, 1., 1.)
        with patch('builtins.print') as output:
            snapshot = self.runtime.process_frame(status_overlay=True)
        self.assertTrue(snapshot.paused)
        self.runtime.overlay.draw.assert_not_called()
        self.runtime.overlay.draw_landmarks.assert_not_called()
        output.assert_not_called()
