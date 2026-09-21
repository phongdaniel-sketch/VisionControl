from types import SimpleNamespace
from unittest.mock import Mock
import unittest
from vision_control.voice_audio import decode


class DecoderDiagnosticsTests(unittest.TestCase):
    def run_decode(self, segments):
        model=Mock()
        model.transcribe.return_value=(iter(segments),SimpleNamespace(duration_after_vad=1.5))
        report=Mock()
        result=decode(model,b'\x00\x10'*32000,16000,diagnostics=report)
        return result,report.call_args.args[0]

    def segment(self, **values):
        base=dict(text='Mấy giờ rồi',start=0.,end=1.,no_speech_prob=.1,avg_logprob=-.3)
        return SimpleNamespace(**(base|values))

    def test_rejected_text_is_logged_without_becoming_command(self):
        result,report=self.run_decode([self.segment(no_speech_prob=.8)])
        self.assertEqual(result,('',0.))
        self.assertEqual(report['rejection'],'no_speech_probability')
        self.assertEqual(report['segments'][0]['text'],'Mấy giờ rồi')

    def test_low_log_probability_has_distinct_reason(self):
        result,report=self.run_decode([self.segment(avg_logprob=-1.2)])
        self.assertEqual(result,('',0.))
        self.assertEqual(report['rejection'],'low_log_probability')

    def test_no_segments_is_distinguishable(self):
        result,report=self.run_decode([])
        self.assertEqual(result,('',0.))
        self.assertEqual(report['rejection'],'no_segments')

    def test_accepted_text_unchanged(self):
        result,report=self.run_decode([self.segment()])
        self.assertEqual(result[0],'Mấy giờ rồi')
        self.assertIsNone(report['rejection'])
