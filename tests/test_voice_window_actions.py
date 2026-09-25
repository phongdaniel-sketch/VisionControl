from unittest.mock import Mock, patch
import test_voice
from vision_control.voice_commands import Command, parse_command


class WindowActionTests(test_voice.VoiceServiceTests):
    def test_phrases(self):
        phrases = ('Đóng cửa sổ', 'Đóng cửa sổ này', 'Đóng cửa sổ đi',
                   'Đóng cửa sổ lại', 'Tắt app.', 'Tắt áp', 'Tắt ứng dụng',
                   'Tắt ứng dụng này', 'Đóng app', 'Đóng ứng dụng')
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assertEqual(parse_command(phrase), Command('close_window'))
        for phrase in ('Đừng tắt app', 'Tắt app rồi khóa máy',
                       'Đừng đóng cửa sổ', 'Tắt áp rồi khóa máy'):
            with self.subTest(phrase=phrase):
                self.assertIsNone(parse_command(phrase))
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
            for paused in (False, True):
                self.window.runtime.paused = paused
                self.window.runtime.set_paused.reset_mock()
                self.window.runtime.adapter.close_window.reset_mock()
                self.service.execute(Command('close_window'))
                self.window.runtime.set_paused.assert_not_called()
                self.window.runtime.adapter.close_window.assert_called_once_with(42)

    def test_lock_dispatches_only_lock(self):
        with patch('vision_control.voice_ui.modifiers_down', return_value=False):
            self.service.execute(Command('lock_computer'))
        self.window.runtime.set_paused.assert_called_with(True)
        self.window.runtime.adapter.lock_computer.assert_called_once()
        self.window.runtime.adapter.perform.assert_not_called()
