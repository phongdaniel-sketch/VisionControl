from datetime import datetime
from unittest.mock import Mock, patch
import unittest
import test_voice
from vision_control.voice_commands import Command, parse_command


class WeekdayParsingTests(unittest.TestCase):
    def test_exact_weekday_phrases_and_accent_error(self):
        for phrase in ('Hôm nay là thứ mấy?', 'Hôm nay là thứ máy.', 'Hôm nay thứ mấy'):
            self.assertEqual(parse_command(phrase), Command('weekday'))

    def test_reject_extra_actions(self):
        self.assertIsNone(parse_command('Hôm nay là thứ mấy rồi copy'))
        self.assertIsNone(parse_command('Đừng hỏi hôm nay là thứ mấy'))


class WeekdayReplyTests(test_voice.VoiceServiceTests):
    def test_weekday_reply(self):
        self.service.reply = Mock()
        with patch('vision_control.voice_ui.datetime') as clock:
            clock.now.return_value = datetime(2026, 9, 21)
            self.service.execute(Command('weekday'))
        self.service.reply.assert_called_once_with('Hôm nay là thứ hai, ngày 21 tháng 9 năm 2026.')
