import unittest
from unittest.mock import patch
import test_voice


class VoiceDiagnosticsTests(test_voice.VoiceServiceTests):
    def test_supported_low_score_shows_reason_without_execution(self):
        with patch.object(self.service, 'execute') as execute:
            self.service.finish(0, 'recognized', ('Mấy giờ rồi', .55))
            execute.assert_not_called()
        self.assertIn('0.550', self.service.last_diagnostic)
        self.assertIn('thấp hơn', self.service.last_diagnostic)

    def test_unknown_phrase_is_not_reported_as_unclear_audio(self):
        self.service.finish(0, 'recognized', ('Thời tiết hôm nay', .8))
        self.assertIn('chưa khớp', self.service.message)
        self.assertIn('Thời tiết hôm nay', self.service.last_diagnostic)

    def test_last_result_survives_ready_status(self):
        self.service.finish(0, 'recognized', ('Mấy giờ rồi', .55))
        diagnostic = self.service.last_diagnostic
        self.service.finish(0, 'spoken', None)
        self.assertEqual(self.service.last_diagnostic, diagnostic)

    def test_stale_result_does_not_replace_diagnostic(self):
        diagnostic = self.service.last_diagnostic
        self.service.disable()
        self.service.finish(0, 'recognized', ('copy', 1))
        self.assertEqual(self.service.last_diagnostic, diagnostic)
