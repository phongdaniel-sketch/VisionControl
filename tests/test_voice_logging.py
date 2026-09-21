import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import unittest
import test_voice
from vision_control.voice_log import append_event


class LogTests(unittest.TestCase):
    def test_json_lines_and_rotation_are_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'voice.jsonl'
            for i in range(180):append_event(path,'recognition',text='x'*2000,score=.6)
            self.assertTrue(Path(str(path)+'.1').exists())
            self.assertLess(path.stat().st_size,262144)
            for line in path.read_text(encoding='utf-8').splitlines():
                self.assertEqual(json.loads(line)['event'],'recognition')


class VoiceLogServiceTests(test_voice.VoiceServiceTests):
    def test_logging_is_disabled_by_default(self):
        self.service.log_event('recognition',text='copy')
        self.assertFalse((self.service.path.parent/'voice_diagnostics.jsonl').exists())

    def test_enabled_logging_records_result(self):
        self.service.config['diagnostic_log']=True
        self.service.preview_only=True
        self.service.finish(0,'recognized',('Mấy giờ rồi',.8))
        row=json.loads((self.service.path.parent/'voice_diagnostics.jsonl').read_text(encoding='utf-8'))
        self.assertEqual(row['command'],'time')
        self.assertTrue(row['preview'])

    def open_dialog(self):
        with patch('vision_control.voice_audio.input_devices',return_value=[(self.service.config['device'],1)]):
            self.service.open_dialog()
        from PySide6.QtWidgets import QPushButton
        return next(b for b in self.service.dialog.findChildren(QPushButton) if b.text()=='Save voice settings')

    def test_save_success_closes_popup(self):
        save=self.open_dialog()
        save.click()
        self.assertIsNone(self.service.dialog)
        self.assertTrue(self.service.path.exists())

    def test_failed_save_keeps_popup_open(self):
        save=self.open_dialog()
        with patch('vision_control.voice_ui._write_json',side_effect=OSError('disk full')):
            save.click()
        self.assertIsNotNone(self.service.dialog)
        self.assertIn('disk full',self.service.message)

    def test_metrics_remain_in_last_result(self):
        self.service.finish(0,'audio_metrics',dict(duration_s=2, speech_s=.8, rms_dbfs=-30, peak_dbfs=-15))
        self.service.finish(0,'recognized',('không',.7))
        self.assertIn('-30.0 dBFS',self.service.last_diagnostic)
