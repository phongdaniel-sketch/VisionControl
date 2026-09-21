from unittest.mock import Mock, patch
import test_voice
from vision_control.voice_commands import Command, parse_command


class WindowActionTests(test_voice.VoiceServiceTests):
    def test_phrases(self):
        self.assertEqual(parse_command('Đóng cửa sổ'), Command('close_window'))
        self.assertEqual(parse_command('Tắt app.'), Command('close_window'))
        self.assertIsNone(parse_command('Đừng tắt app'))
        self.assertIsNone(parse_command('Tắt app rồi khóa máy'))
        for text in ('Khóa máy', 'Khóa máy tính', 'Khóa màn hình'):
            self.assertEqual(parse_command(text), Command('lock_computer'))
        for text in ('Tắt máy', 'shutdown', 'sleep', 'Đừng đóng cửa sổ'):
            self.assertIsNone(parse_command(text))

    def test_close_checks_target(self):
        self.service.target = 42
        self.service.reply = Mock()
        with patch('vision_control.voice_ui.foreground', return_value=43), patch('vision_control.voice_ui.modifiers_down', return_value=False):
            with self.assertRaises(ValueError):
                self.service.execute(Command('close_window'))
        self.window.runtime.adapter.close_window.assert_not_called()
        with patch('vision_control.voice_ui.foreground', return_value=42), patch('vision_control.voice_ui.modifiers_down', return_value=False):
            self.service.execute(Command('close_window'))
        self.window.runtime.adapter.close_window.assert_called_once_with(42)

    def test_lock_dispatches_only_lock(self):
        with patch('vision_control.voice_ui.modifiers_down', return_value=False):
            self.service.execute(Command('lock_computer'))
        self.window.runtime.set_paused.assert_called_with(True)
        self.window.runtime.adapter.lock_computer.assert_called_once()
        self.window.runtime.adapter.perform.assert_not_called()
