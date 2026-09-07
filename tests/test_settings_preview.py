import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from vision_control.settings import DesktopSettings,save_desktop_settings,load_desktop_settings


class SettingsPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def test_camera_names_indices_and_missing_selection(self):
        from vision_control.camera_devices import CameraPicker
        with patch('vision_control.camera_devices.camera_devices',return_value=[(0,'BRIO'),(3,'OBS')]):
            picker=CameraPicker(3)
            self.assertIn('OBS',picker.currentText());self.assertEqual(picker.value(),3)
        with patch('vision_control.camera_devices.camera_devices',return_value=[(0,'BRIO')]):
            picker.refresh();self.assertEqual(picker.value(),3)
            self.assertIn('not currently listed',picker.currentText())
        picker.close()

    def test_preview_preferences_round_trip_and_legacy_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'settings.json'
            p.write_text('{"camera_index": 2}')
            self.assertTrue(load_desktop_settings(p).show_skeleton)
            saved=DesktopSettings(2,True,False,False)
            save_desktop_settings(p,saved)
            self.assertEqual(load_desktop_settings(p),saved)
            self.assertNotIn('debug',p.read_text())

    def test_save_recorder_handoff_does_not_open_camera_twice(self):
        from vision_control.runtime import VisionRuntime
        from vision_control.controller_ui import ControllerWindow
        from vision_control.profile import load_profile
        runtime=VisionRuntime(start_paused=True)
        runtime.profile=load_profile('config/gesture_v1_profile.json')
        runtime.close=Mock()
        window=ControllerWindow(runtime);window.timer.stop()
        with tempfile.TemporaryDirectory() as d:
            import vision_control.settings_ui as ui
            import vision_control.controller_ui as controller_ui
            with patch.object(ui,'USER_PROFILE',Path(d)/'profile.json'), patch.object(ui,'APP_SETTINGS',Path(d)/'settings.json'), patch.object(controller_ui,'APP_SETTINGS',Path(d)/'settings.json'), patch.object(controller_ui,'USER_PROFILE',Path(d)/'profile.json'):
                window.open_settings();settings=window.settings_window
                self.assertNotIn('Keyboard',settings.nav_buttons)
                self.assertIn('Preview & Debug',settings.nav_buttons)
                settings.debug_view.setChecked(True)
                next_runtime=VisionRuntime(start_paused=True)
                next_runtime.start=Mock()
                window.runtime_factory=Mock(return_value=next_runtime)
                with patch('vision_control.diagnostics_ui.DiagnosticWindow') as factory:
                    settings._request_recording()
                    self.app.processEvents()
                    factory.assert_called_once()
                    next_runtime.start.assert_not_called()
                    self.assertTrue(next_runtime.paused)
                    self.assertIsNotNone(window.diagnostic_window)
                window.diagnostic_window=None
        window.close();self.app.processEvents()
