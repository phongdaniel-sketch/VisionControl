import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
import threading
from types import SimpleNamespace
from unittest.mock import Mock, patch

from vision_control.voice_endpoint import VoiceEndpoint
from vision_control.hot_corners import HotCorners
from vision_control.monitors import ScreenRegion
from vision_control.gesture_v1_config import config, validate_action
from vision_control.diagnostics import DiagnosticInputAdapter
import test_voice


class EndpointTests(unittest.TestCase):
    def test_no_speech_deadline(self):
        endpoint = VoiceEndpoint(10)
        self.assertEqual(endpoint.update(14.99, False), '')
        self.assertEqual(endpoint.update(15, False), 'empty')

    def test_silence_finishes_once_speech_started(self):
        endpoint = VoiceEndpoint(0)
        self.assertEqual(endpoint.update(1, True), '')
        self.assertEqual(endpoint.update(2, False), '')
        self.assertEqual(endpoint.update(2.3, False), 'submit')

    def test_pause_resets_when_speech_resumes(self):
        endpoint = VoiceEndpoint(0)
        endpoint.update(1, True)
        endpoint.update(2, True)
        self.assertEqual(endpoint.update(2.3, False), '')

    def test_hard_limit_rejects_even_speech(self):
        endpoint = VoiceEndpoint(0)
        endpoint.update(1, True)
        self.assertEqual(endpoint.update(15, True), 'limit')


class HotCornerTests(unittest.TestCase):
    def setUp(self):
        self.corners = HotCorners()
        self.region = ScreenRegion(-1920, 0, 1920, 1080)

    def update(self, t, point=(-1919, 1), blocked=False):
        return self.corners.update(point, self.region, {'top_left': 'voice_listen_toggle'}, t, blocked=blocked)

    def test_dwell_once_per_entry(self):
        self.assertIsNone(self.update(0))
        self.assertIsNone(self.update(.69))
        self.assertEqual(self.update(.7), 'voice_listen_toggle')
        self.assertIsNone(self.update(10))
        self.update(11, (-1000, 500))
        self.update(12)
        self.assertEqual(self.update(13), 'voice_listen_toggle')

    def test_exit_cancels(self):
        self.update(0)
        self.update(.5, (-1000, 500))
        self.assertIsNone(self.update(.8))
        self.assertIsNone(self.update(1.2))

    def test_blocked_requires_exit(self):
        self.update(0)
        self.update(.5, blocked=True)
        self.assertIsNone(self.update(3))

    def test_outside_fixed_display_does_nothing(self):
        self.assertIsNone(self.update(0, (1, 1)))
        self.assertIsNone(self.update(5, (1, 1)))

    def test_each_corner_and_progress(self):
        for name, point in [('top_left', (-1919, 1)), ('top_right', (-1, 1)),
                            ('bottom_left', (-1919, 1079)), ('bottom_right', (-1, 1079))]:
            corners = HotCorners()
            bindings = {name: 'r'}
            corners.update(point, self.region, bindings, 0)
            corners.update(point, self.region, bindings, .35)
            self.assertAlmostEqual(corners.progress, .5)
            self.assertEqual(corners.update(point, self.region, bindings, 1), 'r')

    def test_old_profile_gets_new_default(self):
        self.assertEqual(config({'corner_seconds': 4})['corner_dwell_seconds'], .7)

    def test_app_actions_do_not_become_keyboard_keys(self):
        adapter = DiagnosticInputAdapter()
        adapter.app_action_handler = Mock()
        for action in ('voice_listen_toggle', 'pause_gestures', 'open_computer'):
            validate_action(action)
            adapter.perform(action)
            adapter.app_action_handler.assert_called_with(action)
        self.assertFalse(adapter.events)


class ToggleServiceTests(test_voice.VoiceServiceTests):
    def test_toggle_disabled_opens_settings_only(self):
        with patch.object(self.service, 'open_dialog') as settings, patch.object(self.service, 'begin') as begin:
            self.service.toggle_listen()
            settings.assert_called_once()
            begin.assert_not_called()

    def test_toggle_starts_automatic(self):
        self.service.config['enabled'] = True
        self.service.state = 'ready'
        with patch.object(self.service, 'begin') as begin:
            self.service.toggle_listen()
            begin.assert_called_once_with(automatic=True)

    def test_cancel_ignores_late_recognition(self):
        self.service.state = 'processing'
        event = self.service.cancel
        self.service.cancel_listen()
        self.assertTrue(event.is_set())
        with patch.object(self.service, 'execute') as execute:
            self.service.finish(0, 'recognized', ('copy', 1))
            execute.assert_not_called()

    def test_second_toggle_submits_without_invalidating_result(self):
        self.service.state='recording'
        generation=self.service.generation
        cancel=self.service.cancel
        self.service.toggle_listen()
        self.assertTrue(self.service.stop_capture.is_set())
        self.assertFalse(cancel.is_set())
        self.assertEqual(self.service.generation,generation)
        self.assertEqual(self.service.state,'processing')
        with patch.object(self.service,'execute') as execute:
            self.service.finish(generation,'recognized',('Mấy giờ rồi',.8))
            self.assertEqual(execute.call_args.args[0].name,'time')

    def test_processing_toggle_is_not_cancellation_or_new_capture(self):
        self.service.state='processing'
        with patch.object(self.service,'begin') as begin:
            self.service.toggle_listen()
            self.service.toggle_listen()
            begin.assert_not_called()
        self.assertFalse(self.service.cancel.is_set())
        self.assertEqual(self.service.generation,0)

    def test_early_submit_ignores_late_micro_ready_progress(self):
        self.service.state='recording'
        self.service.toggle_listen()
        self.service.finish(0,'listening',None)
        self.assertEqual(self.service.state,'processing')
        self.assertIsNone(self.service.listening_started)

    def test_toggle_does_not_depend_on_hotkey_held(self):
        self.service.state = 'recording'
        self.service.automatic = True
        with patch('vision_control.voice_ui.sys.platform', 'linux'):
            self.service.tick()
        self.assertFalse(self.service.stop_capture.is_set())

    def test_hold_mode_still_stops_on_release(self):
        self.service.state = 'recording'
        self.service.automatic = False
        self.service.hotkey = Mock()
        self.service.hotkey.held.return_value = False
        with patch('vision_control.voice_ui.sys.platform', 'linux'):
            self.service.tick()
        self.assertTrue(self.service.stop_capture.is_set())

    def test_settings_micro_refresh_uses_current_devices(self):
        from PySide6.QtWidgets import QComboBox
        with patch('vision_control.voice_audio.input_devices', return_value=[('USB Microphone', 4)]):
            self.service.open_dialog()
        devices = self.service.dialog.findChildren(QComboBox)[0]
        self.assertGreaterEqual(devices.findData('USB Microphone'), 0)
        self.assertFalse(devices.model().item(0).isEnabled())


class CaptureTests(unittest.TestCase):
    def capture(self, speech, automatic=True, cancel=None, overflow=False):
        from vision_control.voice_audio import capture_and_decode
        stream = Mock()
        stream.__enter__ = Mock(return_value=stream)
        stream.__exit__ = Mock(return_value=False)
        stream.read.return_value = (b'\0'*960, overflow)
        stop = threading.Event()
        cancel = cancel or threading.Event()
        with patch('vision_control.voice_audio.input_devices', return_value=[('Test', 1)]), \
             patch('sounddevice.query_devices', return_value={'default_samplerate':16000}), \
             patch('sounddevice.RawInputStream', return_value=stream), \
             patch('webrtcvad.Vad') as vad, \
             patch('vision_control.voice_audio.time.monotonic', side_effect=(i*.03 for i in range(1000))), \
             patch('vision_control.voice_audio.decode', return_value=('copy', 1)) as decode:
            vad.return_value.is_speech.side_effect = speech
            try:
                return capture_and_decode(None, 'Test', stop, cancel, Mock(), automatic), decode
            finally:
                stream.__exit__.assert_called_once()

    def test_no_speech_never_decodes(self):
        with self.assertRaisesRegex(RuntimeError, 'Không nghe'):
            self.capture(lambda *_: False)

    def test_continuous_speech_rejects_truncation(self):
        with self.assertRaisesRegex(RuntimeError, '15'):
            self.capture(lambda *_: True)

    def test_silence_after_speech_decodes(self):
        flags = iter([True]*20+[False]*100)
        result, decode = self.capture(lambda *_: next(flags))
        self.assertEqual(result, ('copy', 1))
        decode.assert_called_once()

    def test_cancel_closes_stream_without_decoding(self):
        cancel = threading.Event();cancel.set()
        result, decode = self.capture(lambda *_: True, cancel=cancel)
        self.assertEqual(result, ('', 0.))
        decode.assert_not_called()

    def test_overflow_aborts(self):
        with self.assertRaisesRegex(RuntimeError, 'mất mẫu'):
            self.capture(lambda *_: True, overflow=True)


class ControllerIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from vision_control.runtime import VisionRuntime
        from vision_control.profile import load_profile
        from vision_control.paths import resource_root
        from vision_control.calibration import MouseCalibration
        from vision_control.controller_ui import ControllerWindow
        self.runtime = VisionRuntime()
        self.runtime.profile = load_profile(resource_root()/'config/default_profile.json')
        self.runtime.profile.gesture_v1.update(enabled=True, corners={'top_left':'r'})
        self.runtime.adapter = DiagnosticInputAdapter()
        self.runtime.adapter.cursor = (1, 1)
        self.runtime.mouse = SimpleNamespace(calibration=MouseCalibration(), release_all=Mock(),
            layout=SimpleNamespace(target=lambda _: ScreenRegion(0, 0, 1920, 1080)))
        self.runtime.started = True
        self.runtime.set_paused(False)
        self.window = ControllerWindow(self.runtime)
        self.window.timer.stop();self.window.corner_timer.stop()
        self.addCleanup(self.window.shutdown)

    def poll(self, stamp):
        with patch('vision_control.controller_ui.time.monotonic', return_value=stamp), \
             patch('vision_control.controller_ui.sys.platform', 'linux'):
            self.window._poll_hot_corners()

    def test_pointer_alone_fires_without_hand_features(self):
        self.poll(0);self.poll(1);self.poll(2)
        self.assertEqual([e['key'] for e in self.runtime.adapter.events if e['action']=='key_down'], ['r'])

    def test_volume_blocks_and_requires_exit(self):
        self.runtime.primary_v1 = SimpleNamespace(mode='volume', gate=SimpleNamespace(name='volume'), reset=Mock())
        self.poll(0);self.poll(1)
        self.runtime.primary_v1.mode = '';self.runtime.primary_v1.gate.name = ''
        self.poll(2)
        self.assertFalse(self.runtime.adapter.events)

    def test_pause_blocks(self):
        self.runtime.set_paused(True)
        self.poll(0);self.poll(1)
        self.assertFalse(self.runtime.adapter.events)

    def test_voice_action_routes_without_keyboard_output(self):
        self.runtime.profile.gesture_v1['corners']['top_left'] = 'voice_listen_toggle'
        with patch.object(self.window, 'toggle_voice_listen') as toggle:
            self.poll(0);self.poll(1)
            self.app.processEvents()
            toggle.assert_called_once()
        self.assertFalse(self.runtime.adapter.events)
