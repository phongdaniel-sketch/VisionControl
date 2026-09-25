import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication, QWidget

from vision_control.voice_commands import Command, Countdown, parse_command
from vision_control.voice_ui import VoiceService
from vision_control.voice_audio import INITIAL_PROMPT


class VoiceCommandTests(unittest.TestCase):
    def test_basic_phrases(self):
        for phrase,name in [('Mở Máy tính','computer'),('Mấy giờ rồi?','time'),
                            ('Hôm nay là ngày mấy','date'),('Copy','copy'),('Sao chép','copy'),
                            ('Paste','paste'),('Dán','paste'),('Hủy hẹn giờ','cancel'),
                            ('Còn bao nhiêu phút','remaining')]:
            with self.subTest(phrase=phrase):self.assertEqual(parse_command(phrase),Command(name))

    def test_relative_timer_numbers(self):
        for phrase,seconds in [('Báo thức sau 10 phút',600),('Báo thức sau mười phút',600),
                               ('Hẹn giờ hai mươi lăm phút',1500),('Hẹn giờ 24 giờ',86400),
                               ('Hẹn giờ một giây',1),('Hẹn giờ chín mươi chín phút',5940)]:
            self.assertEqual(parse_command(phrase),Command('timer',seconds))

    def test_reject_clock_alarm_multiple_actions_negation_and_invalid_timer(self):
        for text in ['Báo thức lúc 7 giờ','Đừng copy','copy paste','Mở máy tính rồi tắt máy',
                     'Hẹn giờ 0 phút','Hẹn giờ 25 giờ','Hẹn giờ -5 phút','Hẹn giờ 1.5 phút',
                     'shutdown /s','Hẹn giờ một trăm phút','Tìm Google']:
            with self.subTest(text=text):self.assertIsNone(parse_command(text))

    def test_local_prompt_covers_sensitive_voice_commands(self):
        for phrase in ('Đóng cửa sổ', 'Tắt app', 'Tắt áp', 'Khóa máy'):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, INITIAL_PROMPT)

    def test_countdown_fires_once_after_sleep(self):
        timer=Countdown();timer.start(600,100)
        self.assertEqual(timer.remaining(110),590)
        self.assertFalse(timer.poll(699))
        self.assertTrue(timer.poll(900))
        self.assertFalse(timer.poll(901))

    def test_replacement_rejected_and_cancel(self):
        timer=Countdown();timer.start(60,100)
        with self.assertRaises(ValueError):timer.start(120,100)
        self.assertEqual(timer.deadline,160)
        timer.cancel();self.assertIsNone(timer.remaining(120))


class VoiceServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path_patch=patch('vision_control.voice_ui.runtime_data_dir',return_value=Path(self.temp.name))
        self.path_patch.start();self.addCleanup(self.path_patch.stop)
        self.window=QWidget()
        self.window.tray=None
        self.window.closing=False
        self.window.runtime=Mock()
        self.window._update_pause_button=Mock();self.window._sync_tray=Mock()
        self.service=VoiceService(self.window)
        self.service.config['speech']=False
        self.service.timer.stop()
        self.addCleanup(self.service.close)
        self.addCleanup(self.window.hide)

    def test_disabled_service_does_not_load_or_listen(self):
        with patch.object(self.service,'run') as run:
            self.service.begin()
            run.assert_not_called()
        self.assertIsNone(self.service.hotkey)

    def test_unknown_or_low_confidence_never_executes(self):
        with patch.object(self.service,'execute') as execute:
            self.service.finish(0,'recognized',('copy',.2))
            self.service.finish(0,'recognized',('không copy',1.))
            execute.assert_not_called()

    def test_stale_result_is_ignored_after_disable(self):
        self.service.disable()
        with patch.object(self.service,'execute') as execute:
            self.service.finish(0,'recognized',('copy',1.))
            execute.assert_not_called()

    def test_preview_never_executes_commands(self):
        self.service.preview_only=True
        with patch.object(self.service,'execute') as execute:
            self.service.finish(0,'recognized',('copy',1.))
            execute.assert_not_called()

    def test_copy_rejects_changed_target_or_held_modifiers(self):
        self.service.target=123
        for target,held in [(456,False),(123,True)]:
            with patch('vision_control.voice_ui.foreground',return_value=target), patch('vision_control.voice_ui.modifiers_down',return_value=held):
                with self.assertRaises(ValueError):self.service.execute(Command('copy'))
        self.window.runtime.adapter.perform.assert_not_called()

    def test_copy_and_paste_preserve_gesture_state_and_use_adapter(self):
        self.service.target=123
        for paused in (False,True):
            for command,action in (('copy','ctrl+c'),('paste','ctrl+v')):
                with self.subTest(paused=paused,command=command):
                    self.window.runtime.paused=paused
                    self.window.runtime.reset_mock()
                    with patch('vision_control.voice_ui.foreground',return_value=123), patch('vision_control.voice_ui.modifiers_down',return_value=False):
                        self.service.execute(Command(command))
                    self.window.runtime.set_paused.assert_not_called()
                    self.assertEqual(self.window.runtime.paused,paused)
                    self.window.runtime.adapter.perform.assert_called_once_with(action)

    def test_speaking_blocks_microphone(self):
        self.service.state='speaking'
        with patch.object(self.service,'run') as run:
            self.service.begin();run.assert_not_called()

    def test_settings_blocks_command_execution(self):
        self.window.settings_window=Mock()
        with patch.object(self.service,'execute') as execute:
            self.service.finish(0,'recognized',('copy',1.))
            execute.assert_not_called()

    def test_alarm_dialog_stop_and_snooze(self):
        from PySide6.QtWidgets import QPushButton
        with patch.object(QApplication,'beep'):
            self.service.ring()
            self.assertIsNotNone(self.service.alarm)
            button=next(b for b in self.service.alarm.findChildren(QPushButton) if '5' in b.text())
            button.click()
            self.assertIsNone(self.service.alarm)
            self.assertIsNotNone(self.service.countdown.deadline)

    def test_hotkey_conflict_shows_error(self):
        self.service.config['enabled']=True
        with patch('vision_control.voice_ui.VoiceHotkey',side_effect=RuntimeError('conflict')):
            self.service.enable()
        self.assertEqual(self.service.state,'off')
        self.assertEqual(self.service.message,'conflict')
