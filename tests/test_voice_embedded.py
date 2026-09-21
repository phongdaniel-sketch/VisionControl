from unittest.mock import patch
from PySide6.QtWidgets import QCheckBox, QLabel, QLineEdit
from PySide6.QtCore import QCoreApplication, QEvent
import test_voice


class EmbeddedVoiceTests(test_voice.VoiceServiceTests):
    def panel(self):
        with patch('vision_control.voice_audio.input_devices', return_value=[('Test', 1)]):
            panel = self.service.open_dialog(embedded=True)
        import shiboken6
        self.addCleanup(lambda: panel.deleteLater() if shiboken6.isValid(panel) else None)
        return panel

    def test_page_does_not_open_popup_or_save_on_creation(self):
        panel = self.panel()
        self.assertIsNone(self.service.dialog)
        self.assertFalse(panel.isWindow() and panel.isVisible())
        self.assertFalse(self.service.path.exists())
        self.assertTrue(panel.apply_voice())
        self.assertFalse(self.service.path.exists())
        texts = '\n'.join(label.text() for label in panel.findChildren(QLabel))
        self.assertIn('Supported commands', texts)
        self.assertIn('Tắt app', texts)
        self.assertIn('Thời tiết hôm nay thế nào', texts)

    def test_save_modified_voice_settings(self):
        panel = self.panel()
        toggle = next(w for w in panel.findChildren(QCheckBox) if w.text()=='Spoken responses')
        toggle.setChecked(True)
        self.assertTrue(panel.apply_voice())
        self.assertTrue(self.service.config['speech'])
        self.assertTrue(self.service.path.exists())

    def test_weather_location_is_saved_with_voice_settings(self):
        panel = self.panel()
        auto = next(w for w in panel.findChildren(QCheckBox)
                    if w.text()=='Automatically detect weather location')
        city = next(w for w in panel.findChildren(QLineEdit)
                    if w.placeholderText()=='Đà Nẵng')
        auto.setChecked(False);city.setText('Hội An')
        self.assertTrue(panel.apply_voice())
        self.assertFalse(self.service.config['weather_auto_location'])
        self.assertEqual(self.service.config['weather_location'], 'Hội An')

    def test_destroy_disconnects_status_callbacks(self):
        panel = self.panel()
        panel.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.service.changed.emit('ready')
        self.service.diagnostic_changed.emit('test')
