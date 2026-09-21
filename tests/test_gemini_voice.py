import base64
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import urllib.error
from unittest.mock import Mock, patch
import wave

from vision_control.voice_hotkey import parse_hotkey
from vision_control.voice_gemini import transcribe, NoRedirect
from vision_control.voice_secret import save_key, load_key, delete_key
import test_voice


class HotkeyTests(unittest.TestCase):
    def test_requested_chords(self):
        for text, mask in [('Ctrl+Shift+Space',6),('Ctrl+Space',2),('Ctrl+Alt+Space',3)]:
            self.assertEqual(parse_hotkey(text),(text,mask,32))

    def test_legacy_and_function_keys(self):
        self.assertEqual(parse_hotkey('V'),('Ctrl+Alt+V',3,86))
        self.assertEqual(parse_hotkey('Space'),('Ctrl+Alt+Space',3,32))
        self.assertEqual(parse_hotkey('shift + ctrl + f8'),('Ctrl+Shift+F8',6,119))

    def test_invalid_chords_rejected(self):
        for text in ('A','Ctrl','Ctrl+Ctrl+Space','Win+Space','Ctrl+Esc','Ctrl+A+B','Ctrl+F13','Ctrl++'):
            with self.subTest(text=text), self.assertRaises(ValueError):parse_hotkey(text)

    def test_native_registration_uses_selected_modifiers(self):
        from vision_control.voice_ui import VoiceHotkey
        with patch('vision_control.voice_ui.sys.platform','win32'), \
             patch('vision_control.voice_ui.ctypes.windll') as windll, \
             patch('vision_control.voice_ui.QApplication.instance'):
            hotkey=VoiceHotkey(Mock(),32,6)
            windll.user32.RegisterHotKey.assert_called_once_with(None,hotkey.ID,0x4006,32)
            hotkey.close()


class GeminiTests(unittest.TestCase):
    def response(self, transcript='Mấy giờ rồi', finish='STOP'):
        response=Mock()
        response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
        response.read.return_value=json.dumps({'candidates':[{'finishReason':finish,
            'content':{'parts':[{'text':json.dumps({'transcript':transcript})}]}}]}).encode()
        return response

    def test_inline_wav_headers_and_no_invented_confidence(self):
        with patch('vision_control.voice_gemini.urllib.request.build_opener') as factory:
            factory.return_value.open.return_value=self.response()
            result=transcribe(b'\0'*3200,16000,'dummy-test-secret',threading.Event())
        self.assertEqual(result,('Mấy giờ rồi',None))
        request=factory.return_value.open.call_args.args[0]
        self.assertNotIn('dummy-test-secret',request.full_url)
        self.assertEqual(request.get_header('X-goog-api-key'),'dummy-test-secret')
        payload=json.loads(request.data)
        audio=payload['contents'][0]['parts'][0]['inlineData']
        with wave.open(io.BytesIO(base64.b64decode(audio['data']))) as wav:
            self.assertEqual(wav.getframerate(),16000)
            self.assertEqual(wav.readframes(1600),b'\0'*3200)

    def test_cancel_prevents_network(self):
        cancel=threading.Event();cancel.set()
        with patch('vision_control.voice_gemini.urllib.request.build_opener') as factory:
            self.assertEqual(transcribe(b'',16000,'dummy',cancel),('',None))
            factory.assert_not_called()

    def test_http_error_does_not_leak_key(self):
        with patch('vision_control.voice_gemini.urllib.request.build_opener') as factory:
            factory.return_value.open.side_effect=urllib.error.HTTPError('secret-in-url',403,'dummy-test-secret',None,None)
            with self.assertRaises(RuntimeError) as error:transcribe(b'\0'*3200,16000,'dummy-test-secret',threading.Event())
        self.assertNotIn('secret',str(error.exception))
        self.assertIn('quyền',str(error.exception))

    def test_truncated_response_rejected(self):
        with patch('vision_control.voice_gemini.urllib.request.build_opener') as factory:
            factory.return_value.open.return_value=self.response(finish='MAX_TOKENS')
            with self.assertRaises(RuntimeError):transcribe(b'\0'*3200,16000,'dummy',threading.Event())

    def test_no_redirects(self):
        self.assertIsNone(NoRedirect().redirect_request(None,None,None,None,None,None))

    @unittest.skipUnless(sys.platform=='win32','Windows DPAPI')
    def test_dpapi_roundtrip_without_plaintext_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.dpapi'
            key='dummy-test-secret-not-a-real-api-key'
            save_key(path,key)
            self.assertNotIn(key.encode(),path.read_bytes())
            self.assertEqual(load_key(path),key)
            delete_key(path)
            self.assertEqual(load_key(path),'')


class GeminiServiceTests(test_voice.VoiceServiceTests):
    def test_default_is_local_without_consent(self):
        self.assertEqual(self.service.config['provider'],'local')
        self.assertFalse(self.service.config['cloud_consent'])

    def test_gemini_never_loads_whisper(self):
        self.service.config.update(enabled=True,provider='gemini',cloud_consent=True)
        with patch('vision_control.voice_ui.VoiceHotkey'), \
             patch('vision_control.voice_ui.voice_secret.load_key',return_value='dummy'), \
             patch.object(self.service,'run') as run:
            self.service.enable()
            self.assertEqual(self.service.state,'ready')
            run.assert_not_called()

    def test_gemini_needs_consent(self):
        self.service.config.update(enabled=True,provider='gemini',cloud_consent=False)
        with patch('vision_control.voice_ui.VoiceHotkey') as hotkey:
            self.service.enable()
            self.assertEqual(self.service.state,'off')
            hotkey.assert_not_called()

    def test_disable_allowed_after_revoking_consent(self):
        config=dict(self.service.config,enabled=False,provider='gemini',cloud_consent=False)
        self.service.configure(config)
        self.assertEqual(self.service.state,'off')

    def test_secret_is_not_in_settings_json(self):
        from PySide6.QtWidgets import QComboBox,QLineEdit,QCheckBox,QPushButton
        with patch('vision_control.voice_audio.input_devices',return_value=[(self.service.config['device'],1)]):
            self.service.open_dialog()
        box=self.service.dialog
        provider=next(w for w in box.findChildren(QComboBox) if w.findData('gemini')>=0)
        provider.setCurrentIndex(provider.findData('gemini'))
        field=next(w for w in box.findChildren(QLineEdit) if w.echoMode()==QLineEdit.EchoMode.Password)
        field.setText('dummy-only-test-key')
        with patch('vision_control.voice_ui.voice_secret.save_key') as save:
            next(w for w in box.findChildren(QPushButton) if w.text()=='Save voice settings').click()
            save.assert_called_once_with(self.service.secret_path,'dummy-only-test-key')
        self.assertNotIn('dummy-only-test-key',self.service.path.read_text())

    def test_none_score_not_accepted_for_local(self):
        with patch.object(self.service,'execute') as execute:
            self.service.finish(0,'recognized',('copy',None))
            execute.assert_not_called()

    def test_gemini_still_rejects_unknown_and_negation(self):
        self.service.config['provider']='gemini'
        with patch.object(self.service,'execute') as execute:
            self.service.finish(0,'recognized',('đừng copy',None))
            execute.assert_not_called()
            self.service.finish(0,'recognized',('Mấy giờ rồi',None))
            self.assertEqual(execute.call_args.args[0].name,'time')
        self.assertIn('không cung cấp điểm',self.service.last_diagnostic)
