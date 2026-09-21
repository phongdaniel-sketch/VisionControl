import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import wave
import threading
from vision_control.voice_recording import VoiceRecording
import test_voice


class RecordingTests(unittest.TestCase):
    def test_timeout_still_delivers_audio_to_recorder(self):
        from vision_control.voice_audio import capture_and_decode
        stream=Mock()
        stream.__enter__=Mock(return_value=stream);stream.__exit__=Mock(return_value=False)
        stream.read.return_value=(b'\0'*960,False)
        recorder=Mock()
        with patch('vision_control.voice_audio.input_devices',return_value=[('Test',1)]), \
             patch('sounddevice.query_devices',return_value={'default_samplerate':16000}), \
             patch('sounddevice.RawInputStream',return_value=stream), \
             patch('webrtcvad.Vad') as vad, \
             patch('vision_control.voice_audio.time.monotonic',side_effect=(i*.03 for i in range(1000))):
            vad.return_value.is_speech.return_value=False
            with self.assertRaises(RuntimeError):
                capture_and_decode(None,'Test',threading.Event(),threading.Event(),Mock(),automatic=True,recording=recorder)
        recorder.assert_called_once()
        self.assertGreater(len(recorder.call_args.args[0]),0)
        self.assertEqual(recorder.call_args.args[1],16000)

    def test_wav_roundtrip_and_linked_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            recording=VoiceRecording(Path(folder),provider='local')
            pcm=b'\x00\x01'*16000
            recording.save_audio(pcm,16000)
            recording.event('recognition',text='Mấy giờ rồi',score=.8)
            with wave.open(str(recording.path)) as audio:
                self.assertEqual(audio.getframerate(),16000)
                self.assertEqual(audio.readframes(16000),pcm)
            rows=[json.loads(line) for line in recording.log_path.read_text(encoding='utf-8').splitlines()]
            self.assertTrue(all(row['capture_id']==recording.id for row in rows))
            self.assertEqual(rows[-1]['text'],'Mấy giờ rồi')

    def test_capacity_refuses_new_samples_without_deleting(self):
        with tempfile.TemporaryDirectory() as folder:
            first=VoiceRecording(Path(folder))
            with patch('vision_control.voice_recording.MAX_SAMPLES',1):
                with self.assertRaises(OSError):VoiceRecording(Path(folder))
            self.assertTrue(first.log_path.exists())

    def test_empty_capture_does_not_create_fake_wav(self):
        with tempfile.TemporaryDirectory() as folder:
            recording=VoiceRecording(Path(folder))
            recording.save_audio(b'',16000)
            self.assertFalse(recording.path.exists())

    def test_storage_budget_refuses_new_capture(self):
        with tempfile.TemporaryDirectory() as folder, patch('vision_control.voice_recording.MAX_BYTES',10):
            with self.assertRaises(OSError):VoiceRecording(Path(folder))


class RecordingServiceTests(test_voice.VoiceServiceTests):
    def test_recording_off_by_default(self):
        self.assertFalse(self.service.config['debug_audio'])

    def test_opt_in_passes_audio_callback_and_preserves_failed_transcription(self):
        self.service.config['debug_audio']=True
        self.service.state='ready'
        self.service.open_debug()
        def capture(*args,**kwargs):
            kwargs['recording'](b'\x00\x01'*1600,16000)
            kwargs['diagnostics']({'rejection':'low_log_probability','segments':[]})
            return '',0.
        with patch.object(self.service,'run',side_effect=lambda kind,fn:fn()), \
             patch('vision_control.voice_audio.capture_and_decode',side_effect=capture):
            self.service.begin(preview=True,debug=True,expected_text='Mấy giờ rồi')
        recording=self.service.active_recording
        self.assertTrue(recording.path.exists())
        self.assertIn('low_log_probability',recording.log_path.read_text(encoding='utf-8'))

    def test_disabled_recording_passes_no_callback(self):
        self.service.config['debug_audio']=True  # Legacy setting must no longer enable saving.
        self.service.state='ready'
        with patch.object(self.service,'run',side_effect=lambda kind,fn:fn()), \
             patch('vision_control.voice_audio.capture_and_decode',return_value=('',0)) as capture:
            self.service.begin(preview=True)
        self.assertIsNone(capture.call_args.kwargs['recording'])
        self.assertFalse((self.service.path.parent/'voice_debug').exists())

    def test_debug_flag_requires_dedicated_dialog(self):
        self.service.state='ready'
        with patch.object(self.service,'run') as run:
            self.service.begin(debug=True)
            run.assert_not_called()

    def test_debug_open_blocks_normal_hotkey(self):
        self.service.state='ready'
        self.service.open_debug()
        with patch.object(self.service,'run') as run:
            self.service.begin()
            self.service.toggle_listen()
            run.assert_not_called()

    def test_debug_always_preview_and_never_executes(self):
        self.service.state='ready';self.service.open_debug()
        with patch.object(self.service,'run'),patch.object(self.service,'execute') as execute:
            self.service.begin(debug=True)
            self.service.finish(self.service.generation,'recognized',('Mấy giờ rồi',.9))
            execute.assert_not_called()
        self.assertTrue(self.service.preview_only)

    def test_debug_close_cancels_current_capture(self):
        self.service.state='ready';self.service.open_debug()
        with patch.object(self.service,'run'):
            self.service.begin(debug=True)
        event=self.service.cancel
        self.service.debug_dialog.close()
        self.assertTrue(event.is_set())
        self.assertIsNone(self.service.debug_dialog)
