import tempfile
import threading
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
from vision_control.voice_audio import mono_channel, capture_and_decode
from vision_control.voice_recording import VoiceRecording


class StereoTests(unittest.TestCase):
    def test_channel_one_preserved_even_with_opposite_phase(self):
        left = np.array([100, -200, 300], dtype='<i2')
        stereo = np.column_stack((left, -left)).astype('<i2').tobytes()
        self.assertEqual(mono_channel(stereo, 2), left.tobytes())
        self.assertEqual(mono_channel(left.tobytes(), 1), left.tobytes())
        with self.assertRaises(ValueError):
            mono_channel(b'123', 2)

    def test_stereo_wav_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            recording = VoiceRecording(Path(folder))
            pcm = np.tile(np.array([100, -100], dtype='<i2'), 16000).tobytes()
            recording.save_audio(pcm, 16000, 2)
            with wave.open(str(recording.path)) as wav:
                self.assertEqual(wav.getnchannels(), 2)
                self.assertEqual(wav.getnframes(), 16000)
                self.assertEqual(wav.readframes(16000), pcm)

    def test_capture_records_stereo_but_decodes_mono(self):
        stop = threading.Event()
        raw = np.tile(np.array([1000, -2000], dtype='<i2'), 480).tobytes()
        stream = Mock()
        stream.__enter__ = Mock(return_value=stream)
        stream.__exit__ = Mock(return_value=False)
        count = 0
        def read(frames):
            nonlocal count
            count += 1
            if count == 5:
                stop.set()
            return raw, False
        stream.read.side_effect = read
        recording, metrics = Mock(), Mock()
        decoder = Mock(return_value=('test', 1))
        with patch('vision_control.voice_audio.input_devices', return_value=[('Test', 1)]), \
             patch('sounddevice.query_devices', return_value=dict(default_samplerate=16000, max_input_channels=2)), \
             patch('sounddevice.RawInputStream', return_value=stream) as factory, \
             patch('webrtcvad.Vad') as vad:
            vad.return_value.is_speech.return_value = True
            capture_and_decode(None, 'Test', stop, threading.Event(), Mock(),
                               decoder=decoder, recording=recording, metrics=metrics)
        self.assertEqual(factory.call_args.kwargs['channels'], 2)
        recording.assert_called_once_with(raw * 5, 16000, 2)
        decoder.assert_called_once_with(mono_channel(raw, 2) * 5, 16000)
        self.assertEqual(len(metrics.call_args.args[0]['channel_levels']), 2)


if __name__ == '__main__':
    unittest.main()
