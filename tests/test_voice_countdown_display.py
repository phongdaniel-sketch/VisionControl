from unittest.mock import patch, Mock
import test_voice
from vision_control.voice_commands import Command, parse_command


class CountdownDisplayTests(test_voice.VoiceServiceTests):
    def test_display_start_cancel_expire(self):
        self.service.reply = Mock()
        with patch('vision_control.voice_ui.time.time', return_value=100):
            self.service.execute(Command('timer', 65))
            self.assertEqual(self.service.countdown_label.text(), 'Hẹn giờ  00:01:05')
            self.assertTrue(self.service.countdown_label.isVisible())
            self.service.execute(Command('cancel'))
            self.assertFalse(self.service.countdown_label.isVisible())
            self.service.execute(Command('timer', 1))
        with patch('vision_control.voice_ui.time.time', return_value=102), patch.object(self.service, 'ring') as ring:
            self.service.tick()
            ring.assert_called_once()
            self.assertFalse(self.service.countdown_label.isVisible())

    def test_paste_aliases_remain_exact(self):
        for phrase in ('Dán', 'Dán nội dung', 'Dán văn bản', 'Dạ', 'Dạ.'):
            self.assertEqual(parse_command(phrase), Command('paste'))
        for phrase in ('Dạ vâng', 'Đừng dạ', 'Sao', 'Đừng dán nội dung', 'Dán văn bản rồi copy'):
            self.assertIsNone(parse_command(phrase))
