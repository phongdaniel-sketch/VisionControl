"""Qt-owned voice lifecycle, local by default with explicit cloud opt-in."""
import ctypes
from ctypes import wintypes
from datetime import datetime
import json
import subprocess
import sys
import threading
import time

from PySide6.QtCore import QObject, Signal, QTimer, QAbstractNativeEventFilter, Qt
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QFormLayout,
                              QLabel, QCheckBox, QComboBox, QPushButton, QLineEdit, QScrollArea, QWidget, QPlainTextEdit)
from .paths import runtime_data_dir
from .settings import _write_json
from .voice_commands import Countdown, parse_command
from . import voice_audio
from .voice_hotkey import parse_hotkey
from . import voice_secret


def foreground():
    if sys.platform != 'win32': return 0
    api = ctypes.windll.user32
    api.GetForegroundWindow.restype = wintypes.HWND
    return api.GetForegroundWindow()


def modifiers_down():
    return any(ctypes.windll.user32.GetAsyncKeyState(k) & 0x8000
               for k in (0x10,0x11,0x12,0x5B,0x5C))


class VoiceHotkey(QAbstractNativeEventFilter):
    ID = 0x5643

    def __init__(self, service, key, modifiers=3):
        super().__init__()
        self.service, self.key = service, key
        self.active = False
        if sys.platform != 'win32':
            raise RuntimeError('Hotkey giọng nói hiện chỉ hỗ trợ Windows.')
        if not ctypes.windll.user32.RegisterHotKey(None, self.ID, 0x4000 | modifiers, key):
            raise RuntimeError('Hotkey đang được ứng dụng khác sử dụng. Hãy chọn phím khác.')
        self.active = True
        QApplication.instance().installNativeEventFilter(self)

    def nativeEventFilter(self, event_type, message):
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == 0x312 and msg.wParam == self.ID:
            self.service.begin()
            return True, 0
        return False, 0

    def held(self):
        return bool(ctypes.windll.user32.GetAsyncKeyState(self.key) & 0x8000)

    def close(self):
        if self.active:
            ctypes.windll.user32.UnregisterHotKey(None, self.ID)
            QApplication.instance().removeNativeEventFilter(self)
            self.active = False


class VoiceService(QObject):
    changed = Signal(str)
    diagnostic_changed = Signal(str)
    completed = Signal(int, str, object)

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.path = runtime_data_dir()/'voice_settings.json'
        self.config = dict(enabled=False, device='Microphone (Logitech BRIO)', hotkey='Space', speech=True)
        self.config['diagnostic_log'] = False
        self.config['debug_audio'] = False
        self.config.update(provider='local', cloud_consent=False,
                           weather_auto_location=True, weather_location='Đà Nẵng')
        self.secret_path = self.path.parent/'gemini_key.dpapi'
        try:
            if self.path.exists():
                raw=json.loads(self.path.read_text(encoding='utf-8'))
                for key in self.config:
                    if key in raw and isinstance(raw[key],type(self.config[key])):self.config[key]=raw[key]
        except (OSError, ValueError): pass
        try:self.config['hotkey'] = parse_hotkey(self.config['hotkey'])[0]
        except ValueError:self.config['hotkey'] = 'Ctrl+Alt+Space'
        if self.config['provider'] not in ('local', 'gemini'):self.config['provider']='local'
        self.hotkey = None
        self.model = None
        self.dialog = self.alarm = None
        self.debug_dialog = None
        self.state = 'off'
        self.message = 'Voice Control đang tắt.'
        self.last_diagnostic = 'Chưa có kết quả nhận diện trong phiên này.'
        self.last_audio = ''
        self.active_recording = None
        self.generation = 0
        self.cancel = threading.Event()
        self.stop_capture = threading.Event()
        self.workers = []
        self.countdown = Countdown()
        self.target = 0
        self.preview_only = False
        self.automatic = False
        self.listening_started = None
        self.remaining_label = None
        self.closed = False
        self.bubble=QLabel('',window)
        self.bubble.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.bubble.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.bubble.setWordWrap(True)
        self.bubble.setFixedWidth(420)
        self.bubble.setStyleSheet('QLabel {background: #20242b; color: white; padding: 14px;}')
        self.bubble_timer=QTimer(self)
        self.bubble_timer.setSingleShot(True)
        self.bubble_timer.timeout.connect(self.bubble.hide)
        self.countdown_label = QLabel('', window)
        self.countdown_label.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.countdown_label.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.countdown_label.setFixedSize(240, 48)
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet('QLabel {background: #20242b; color: white; padding: 8px;}')
        self.countdown_display_seconds = None
        self.completed.connect(self.finish)
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        if self.config['enabled']:
            QTimer.singleShot(0,self.enable)

    def diagnostic(self, message):
        # Keep only the last result in memory, never store speech or transcripts.
        self.last_diagnostic = message + ('\n'+self.last_audio if self.last_audio else '')
        self.diagnostic_changed.emit(self.last_diagnostic)

    def log_event(self, event, **fields):
        if self.active_recording is not None and event in ('recognition','capture_submit','capture_cancel','error'):
            try:self.active_recording.event(event,**fields)
            except (OSError,ValueError):pass
        if not self.config.get('diagnostic_log', False):return
        from .voice_log import append_event
        try:
            append_event(self.path.parent/'voice_diagnostics.jsonl', event,
                         capture_id=self.active_recording.id if self.active_recording else None, **fields)
        except (OSError, ValueError) as exc:
            self.status(f'Không ghi được log chẩn đoán: {exc}')

    def status(self, message):
        self.message = message
        self.changed.emit(message)
        button = getattr(self.window, 'voice_button', None)
        if button is not None:
            labels = {'off': 'Voice · Off', 'ready': 'Voice', 'loading': 'Voice · Loading',
                      'recording': 'Voice · Gửi lệnh', 'processing': 'Voice · Đang xử lý',
                      'speaking': 'Voice · Speaking', 'cancelling': 'Voice · Cancelling'}
            button.setText(labels.get(self.state, 'Voice'))
            button.setEnabled(self.state in ('off', 'ready', 'recording'))
            button.setToolTip('Bấm để kết thúc thu và xử lý lệnh. Esc để hủy.' if self.state=='recording' else message)
        if not self.closed and QApplication.platformName() != 'offscreen':
            self.bubble.setText(message)
            self.bubble.adjustSize()
            area=self.window.screen().availableGeometry()
            self.bubble.move(area.right()-self.bubble.width()-20,area.top()+24)
            self.bubble.show()
            self.bubble_timer.start(12000 if self.state in ('recording','processing','loading') else 5000)
        if self.window.tray is not None:
            self.window.tray.voice_action.setText('Voice: '+message[:90])

    def run(self, kind, operation):
        generation = self.generation
        def deliver(kind, value):
            if self.closed:return
            try:self.completed.emit(generation,kind,value)
            except RuntimeError:pass  # Qt owner may already have closed.
        def worker():
            try: value=operation()
            except Exception as exc: deliver('error',str(exc))
            else:deliver(kind,value)
        self.workers=[t for t in self.workers if t.is_alive()]
        thread=threading.Thread(target=worker,daemon=False)
        self.workers.append(thread)
        thread.start()

    def enable(self):
        if self.closed or not self.config['enabled']:return
        try:
            name, modifiers, key = parse_hotkey(self.config['hotkey'])
            if self.config.get('provider') == 'gemini':
                if not self.config.get('cloud_consent'):
                    raise ValueError('Cần đồng ý gửi âm thanh tới Google để dùng Gemini.')
                if not voice_secret.load_key(self.secret_path):
                    raise ValueError('Chưa có Gemini API key.')
            self.hotkey=VoiceHotkey(self,key,modifiers)
            if self.config.get('provider') == 'gemini' or self.model is not None:
                self.state='ready'
                self.status('Sẵn sàng: giữ '+name)
                return
            self.state='loading'
            self.status('Đang nạp model tiếng Việt...')
            self.run('loaded',voice_audio.load_model)
        except Exception as exc:
            if self.hotkey:self.hotkey.close()
            self.hotkey=None
            self.state='off'
            self.status(str(exc))

    def configure(self, config):
        config = dict(config)
        config['hotkey'] = parse_hotkey(config['hotkey'])[0]
        if config.get('provider', 'local') not in ('local', 'gemini'):
            raise ValueError('Dịch vụ nhận diện không hợp lệ.')
        if config['enabled'] and config.get('provider') == 'gemini':
            if not config.get('cloud_consent') or not voice_secret.load_key(self.secret_path):
                raise ValueError('Gemini cần API key và đồng ý gửi âm thanh.')
        self.disable()
        _write_json(self.path,config)
        self.config=config
        if config['enabled']:self.enable()
        if config['enabled'] and self.state=='off':raise ValueError(self.message)

    def disable(self):
        self.generation += 1
        self.cancel.set()
        self.stop_capture.set()
        if self.hotkey:self.hotkey.close()
        self.hotkey=None
        self.state='off'
        self.status('Voice Control đang tắt.')
        # Old workers retain their own cancellation event.
        self.cancel=threading.Event()
        self.stop_capture=threading.Event()

    def blocked(self):
        w=self.window
        return w.closing or self.dialog is not None or self.debug_dialog is not None or any(getattr(w,n,None) is not None for n in
                                ('settings_window','diagnostic_window','pose_window'))

    def toggle_listen(self):
        if self.debug_dialog is not None:return
        if self.state == 'recording':
            self.submit_listen()
        elif self.state in ('processing', 'cancelling', 'speaking', 'loading'):
            return
        elif not self.config['enabled']:
            self.open_dialog()
        else:
            self.begin(automatic=True)

    def submit_listen(self):
        if self.state != 'recording':return
        self.stop_capture.set()
        self.listening_started=None
        self.state='processing'
        self.log_event('capture_submit', source='toggle')
        self.status('Đang kết thúc thu và nhận diện...')

    def cancel_listen(self):
        if self.state not in ('recording', 'processing'):
            return
        self.log_event('capture_cancel')
        self.generation += 1
        self.cancel.set()
        self.stop_capture.set()
        self.cancel = threading.Event()
        self.listening_started = None
        self.state = 'cancelling'
        self.status('Đã hủy lệnh. Đang đóng micro...')

    def begin(self, preview=False, automatic=False, debug=False, expected_text=''):
        if debug:
            if self.debug_dialog is None:return
            preview=True
        if self.closed or self.state!='ready' or (not preview and (self.blocked() or self.alarm is not None)):
            return
        if any(worker.is_alive() for worker in self.workers):
            return
        self.target=foreground()
        self.preview_only=preview
        self.automatic=automatic
        self.listening_started=None
        self.remaining_label=None
        self.last_audio=''
        provider = self.config.get('provider', 'local')
        self.active_recording=None
        if debug:
            from .voice_recording import VoiceRecording
            try:
                self.active_recording=VoiceRecording(self.path.parent/'voice_debug',
                    device=self.config['device'], provider=provider, preview=preview, automatic=automatic,
                    expected_text=expected_text[:1000])
            except OSError as exc:
                self.status(str(exc));return
        recording=self.active_recording
        self.log_event('capture_start', device=self.config['device'], automatic=automatic, preview=preview, provider=provider)
        self.state='recording'
        self.stop_capture=threading.Event()
        stop,cancel=self.stop_capture,self.cancel
        generation=self.generation
        self.status('Đang mở micro...')
        def progress(stage, value=None):
            if recording is not None:
                try:recording.event(stage, **(value if isinstance(value,dict) else {'value':value}))
                except (OSError,ValueError):pass
            if not self.closed:
                try:self.completed.emit(generation,stage,value)
                except RuntimeError:pass
        model, device = self.model, self.config['device']
        consent = self.config.get('cloud_consent', False)
        def capture():
            decoder = None
            if provider == 'gemini':
                if not consent:raise RuntimeError('Chưa đồng ý gửi âm thanh tới Google.')
                key = voice_secret.load_key(self.secret_path)
                if not key:raise RuntimeError('Chưa có Gemini API key.')
                from .voice_gemini import transcribe
                decoder = lambda data, rate: transcribe(data, rate, key, cancel)
            def save_audio(data, rate, channels=1):
                try:
                    recording.save_audio(data,rate,channels)
                    progress('recording_saved',str(recording.path) if data else '')
                except (OSError,ValueError) as exc:
                    progress('recording_error',str(exc))
            try:
                result=voice_audio.capture_and_decode(model,device,stop,cancel,
                    progress, automatic=automatic, metrics=lambda value: progress('audio_metrics', value), decoder=decoder,
                    diagnostics=lambda value: progress('decoder_metrics', value),
                    recording=save_audio if recording else None)
            except Exception as exc:
                progress('capture_error',str(exc))
                raise
            if recording is not None:
                try:recording.event('capture_result',text=result[0],score=result[1],cancelled=cancel.is_set())
                except (OSError,ValueError):pass
            return result
        self.run('recognized',capture)

    def finish(self, generation, kind, value):
        if self.closed or generation!=self.generation:return
        if kind in ('recording_saved','recording_error'):
            self.log_event(kind,path=value) if kind=='recording_saved' else self.log_event(kind,message=value)
            if kind=='recording_error':
                self.diagnostic('Không lưu được WAV debug: '+str(value))
                self.status('Không lưu được WAV debug: '+str(value))
            return
        if kind=='capture_error':return
        if kind=='decoder_metrics':
            self.log_event('decoder_metrics', **value)
            return
        if kind=='audio_metrics':
            self.log_event('audio_metrics', **value)
            self.last_audio = (f'Thu: {value["duration_s"]:.2f}s · Tiếng nói: {value["speech_s"]:.2f}s · '
                               f'Mức âm: {value["rms_dbfs"]:.1f} dBFS · Đỉnh: {value["peak_dbfs"]:.1f} dBFS')
            return
        if kind=='listening':
            if self.state != 'recording':return
            self.listening_started=time.monotonic()
            self.status('Đang nghe...' if not self.preview_only else 'Đang nghe thử, không thực thi lệnh...')
            return
        if kind=='processing':
            self.state='processing'
            self.status('Đang nhận diện...')
            return
        if kind=='error':
            self.log_event('error', message=str(value))
            self.state='ready' if self.hotkey and (self.model is not None or self.config.get('provider')=='gemini') else 'off'
            self.diagnostic(f'Lỗi: {value}\nMicro: {self.config["device"]}')
            self.status(str(value))
            return
        if kind=='loaded':
            self.model=value
            self.state='ready'
            self.status('Sẵn sàng: giữ '+self.config['hotkey'])
        elif kind=='spoken':
            self.state='ready' if self.hotkey else 'off'
            self.status('Sẵn sàng.' if self.hotkey else 'Voice Control đang tắt.')
        elif kind=='weather':
            self.state='ready'
            self.reply(value)
        elif kind=='recognized':
            self.state='ready'
            text,confidence=value
            parsed = parse_command(text)
            gemini = self.config.get('provider') == 'gemini'
            accepted_score = (gemini and confidence is None) or (confidence is not None and confidence >= .6)
            command = parsed if accepted_score else None
            if not text:
                reason = 'Không có lời nói được nhận diện.'
            elif not accepted_score:
                reason = 'Điểm nhận diện thấp hơn ngưỡng 0.60; không thực hiện lệnh.'
            elif parsed is None:
                reason = 'Câu nói chưa khớp lệnh được hỗ trợ.'
            else:
                reason = f'Nhận dạng lệnh: {parsed.name}'
            self.log_event('recognition', text=text[:2000], score=confidence, reason=reason,
                           command=command.name if command else None, preview=self.preview_only)
            score_text = 'Gemini: không cung cấp điểm nhận diện' if confidence is None else f'Điểm nhận diện: {confidence:.3f} (ngưỡng 0.60, không phải xác suất chính xác)'
            self.diagnostic(f'Nghe: {text or "(trống)"}\n{score_text}\n'
                            f'{reason}\nMicro: {self.config["device"]}' + ('\nChế độ thử: không thực hiện lệnh.' if self.preview_only else ''))
            self.status(f'Nghe: {text or "(không rõ)"}')
            if self.preview_only:
                self.status(f'Nghe: {text or "(không rõ)"} | Lệnh: {command.name if command else "không nhận"}')
            elif command is None:
                self.reply('Câu nói chưa khớp lệnh được hỗ trợ.' if text and accepted_score
                           else 'Chưa nghe rõ lệnh. Bạn vui lòng nói lại.')
            elif self.blocked() or self.alarm is not None:
                self.status('Đã hủy lệnh vì có cửa sổ thao tác khác.')
            else:
                try:self.execute(command)
                except Exception as exc:self.reply(str(exc))

    def reply(self, text):
        should_speak = self.config['speech'] and self.state not in ('speaking','recording')
        if should_speak:
            self.state='speaking'
        self.status(text)
        if self.window.tray is not None:
            self.window.tray.icon.showMessage('VisionControl',text)
        if should_speak:
            cancel=self.cancel
            self.run('spoken',lambda:voice_audio.speak(text,cancel))

    def execute(self, command):
        name=command.name
        now=datetime.now()
        if name=='time':self.reply(f'Bây giờ là {now.hour} giờ {now.minute} phút.')
        elif name=='date':self.reply(f'Hôm nay là ngày {now.day} tháng {now.month} năm {now.year}.')
        elif name=='weekday':
            weekdays=('thứ hai','thứ ba','thứ tư','thứ năm','thứ sáu','thứ bảy','chủ nhật')
            self.reply(f'Hôm nay là {weekdays[now.weekday()]}, ngày {now.day} tháng {now.month} năm {now.year}.')
        elif name=='computer':
            subprocess.Popen(['explorer.exe','shell:MyComputerFolder'])
            self.reply('Đã mở Máy tính.')
        elif name=='weather':
            from .voice_weather import safe_weather_report
            self.state='processing'
            self.status('Đang tra cứu thời tiết...')
            self.run('weather', lambda: safe_weather_report(
                self.config.get('weather_location', 'Đà Nẵng'),
                self.config.get('weather_auto_location', True)))
        elif name in ('close_window', 'lock_computer'):
            if modifiers_down() or (name=='close_window' and (not self.target or foreground()!=self.target)):
                raise ValueError('Đã hủy: cửa sổ đích thay đổi hoặc bạn chưa thả phím bổ trợ.')
            self.window.runtime.set_paused(True)
            self.window._update_pause_button()
            self.window._sync_tray()
            if name=='close_window':
                self.window.runtime.adapter.close_window(self.target)
                self.reply('Đã gửi yêu cầu đóng cửa sổ.')
            else:
                self.window.runtime.adapter.lock_computer()
                self.status('Đã gửi yêu cầu khóa máy. Điều khiển tay đã tạm dừng.')
        elif name in ('copy','paste'):
            if not self.target or foreground()!=self.target or modifiers_down():
                raise ValueError('Đã hủy: cửa sổ đích thay đổi hoặc bạn chưa thả phím bổ trợ.')
            self.window.runtime.set_paused(True)
            self.window._update_pause_button()
            self.window._sync_tray()
            self.window.runtime.adapter.perform('ctrl+c' if name=='copy' else 'ctrl+v')
            self.reply('Đã gửi lệnh '+('sao chép' if name=='copy' else 'dán')+'. Điều khiển tay đã tạm dừng.')
        elif name=='timer':
            self.countdown.start(command.seconds,time.time())
            self.update_countdown_display()
            self.reply(f'Đã đặt hẹn giờ {command.seconds//60} phút.' if command.seconds%60==0
                       else f'Đã đặt hẹn giờ {command.seconds} giây.')
        elif name=='cancel':
            had=self.countdown.deadline is not None
            self.countdown.cancel()
            self.update_countdown_display()
            self.reply('Đã hủy hẹn giờ.' if had else 'Không có hẹn giờ đang chạy.')
        elif name=='remaining':
            seconds=self.countdown.remaining(time.time())
            self.reply('Không có hẹn giờ đang chạy.' if seconds is None else
                       f'Còn {seconds//60} phút {seconds%60} giây.')

    def update_countdown_display(self):
        seconds = self.countdown.remaining(time.time())
        if seconds is None:
            self.countdown_label.hide()
            self.countdown_display_seconds = None
            return
        if seconds == self.countdown_display_seconds:return
        self.countdown_display_seconds = seconds
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.countdown_label.setText(f'Hẹn giờ  {hours:02d}:{minutes:02d}:{seconds:02d}')
        area = self.window.screen().availableGeometry()
        self.countdown_label.move(area.right()-self.countdown_label.width()-20, area.bottom()-self.countdown_label.height()-20)
        self.countdown_label.show()

    def tick(self):
        if self.closed:return
        if self.state in ('recording', 'processing') and sys.platform == 'win32':
            if ctypes.windll.user32.GetAsyncKeyState(0x1B) & 0x8000:
                self.cancel_listen()
        if self.state == 'cancelling' and not any(t.is_alive() for t in self.workers):
            self.state = 'ready' if self.hotkey else 'off'
            self.status('Đã hủy. Sẵn sàng.' if self.hotkey else 'Voice Control đang tắt.')
        if self.state=='recording' and not self.preview_only and not self.automatic and (not self.hotkey or not self.hotkey.held()):
            self.stop_capture.set()
        if self.state == 'recording' and self.listening_started is not None:
            remaining = max(0, 15-int(time.monotonic()-self.listening_started))
            if remaining != self.remaining_label:
                self.remaining_label = remaining
                self.status(f'Đang nghe · {remaining} giây' + (' · Thử micro' if self.preview_only else ''))
                button = getattr(self.window, 'voice_button', None)
                if button is not None:button.setText(f'Gửi lệnh · {remaining}s')
        if self.countdown.poll(time.time()):self.ring()
        self.update_countdown_display()

    def ring(self):
        if self.alarm is not None:return
        # Invalidate any in-flight recognition before showing an alarm.
        self.generation+=1
        self.cancel.set();self.stop_capture.set()
        self.cancel=threading.Event()
        self.state='ready' if self.hotkey else 'off'
        box=QDialog(self.window)
        box.setWindowTitle('Hết thời gian hẹn giờ')
        layout=QVBoxLayout(box)
        layout.addWidget(QLabel('Đã hết thời gian hẹn giờ.'))
        stop=QPushButton('Dừng');snooze=QPushButton('Nhắc lại sau 5 phút')
        layout.addWidget(stop);layout.addWidget(snooze)
        stop.clicked.connect(box.accept)
        def later():
            self.countdown.start(300,time.time())
            box.accept()
        snooze.clicked.connect(later)
        bell=QTimer(box);bell.setInterval(2000);bell.timeout.connect(QApplication.beep)
        def done():
            bell.stop();self.alarm=None;box.deleteLater()
        box.finished.connect(done)
        self.alarm=box
        box.show();box.raise_()
        QApplication.beep();bell.start()
        self.reply('Đã hết thời gian hẹn giờ.')

    def open_debug(self):
        if self.debug_dialog is not None:
            self.debug_dialog.show();self.debug_dialog.raise_();return
        if self.state in ('recording','processing','speaking','cancelling'):
            self.status('Hãy kết thúc lượt Voice hiện tại trước khi mở Debug.');return
        box=QDialog(self.window);box.setWindowTitle('Voice Debug')
        box.resize(620,500)
        layout=QVBoxLayout(box)
        form=QFormLayout();layout.addLayout(form)
        form.addRow('Micro',QLabel(self.config['device']))
        form.addRow('Speech-to-Text',QLabel(self.config.get('provider','local')))
        form.addRow(QLabel('Debug · Không thực thi lệnh'))
        expected=QLineEdit();expected.setMaxLength(1000)
        form.addRow('Câu sẽ đọc',expected)
        persist=QCheckBox('Lưu mẫu WAV + log cục bộ');persist.setChecked(True)
        form.addRow(persist)
        status=QLabel(self.message);status.setWordWrap(True)
        self.changed.connect(status.setText);layout.addWidget(status)
        result=QPlainTextEdit();result.setReadOnly(True)
        result.setPlainText(self.last_diagnostic)
        self.diagnostic_changed.connect(result.setPlainText);layout.addWidget(result)
        capture=QPushButton('Giữ để thu mẫu debug')
        capture.setObjectName('voice_debug_capture')
        def start():
            if self.state!='ready':
                self.status('Voice chưa sẵn sàng. Hãy bật và lưu cấu hình Voice trước.');return
            self.begin(preview=True,debug=persist.isChecked(),expected_text=expected.text())
        capture.pressed.connect(start)
        capture.released.connect(self.stop_debug_capture)
        layout.addWidget(capture)
        folder=QPushButton('Mở thư mục mẫu debug')
        folder.clicked.connect(self.open_recording_folder);layout.addWidget(folder)
        close=QPushButton('Đóng');close.clicked.connect(box.reject);layout.addWidget(close)
        def done():
            if self.preview_only:self.cancel_listen()
            self.changed.disconnect(status.setText)
            self.diagnostic_changed.disconnect(result.setPlainText)
            self.debug_dialog=None
            box.deleteLater()
        box.finished.connect(done)
        self.debug_dialog=box;box.show()

    def stop_debug_capture(self):
        if self.preview_only and self.state=='recording':self.stop_capture.set()

    def open_recording_folder(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        root=self.path.parent/'voice_debug'
        try:
            root.mkdir(parents=True,exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(root)))
        except OSError as exc:self.status(str(exc))

    def open_dialog(self, embedded=False):
        if not embedded and self.dialog is not None:
            self.dialog.show();self.dialog.raise_();return
        box=QWidget() if embedded else QDialog(self.window)
        box.setWindowTitle('Voice')
        area=self.window.screen().availableGeometry()
        box.resize(min(680,area.width()-60),min(760,area.height()-80))
        outer=QVBoxLayout(box)
        scroll=QScrollArea();scroll.setWidgetResizable(True)
        content=QWidget();form=QFormLayout(content)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        if embedded:
            outer.addWidget(content)
            scroll.deleteLater()
        else:
            scroll.setWidget(content);outer.addWidget(scroll)
        enabled=QCheckBox('Enable voice control');enabled.setChecked(self.config['enabled'])
        speech=QCheckBox('Spoken responses');speech.setChecked(self.config['speech'])
        logging=QCheckBox('Diagnostic logging')
        logging.setChecked(self.config.get('diagnostic_log', False))
        logging.setToolTip(str(self.path.parent/'voice_diagnostics.jsonl'))
        debug_button=QPushButton('Voice Debug...')
        debug_button.clicked.connect(self.open_debug)
        devices=QComboBox()
        def refresh_devices():
            selected = devices.currentData() or self.config['device']
            devices.clear()
            try:
                for name,_ in voice_audio.input_devices():devices.addItem(name, name)
            except Exception as exc:self.status(str(exc))
            index = devices.findData(selected)
            if index < 0:
                devices.insertItem(0, selected+' (disconnected)', selected)
                devices.model().item(0).setEnabled(False)
                index = 0
            devices.setCurrentIndex(index)
        refresh_devices()
        refresh=QPushButton('Refresh microphones');refresh.clicked.connect(refresh_devices)
        hotkey=QComboBox();hotkey.setEditable(True)
        hotkey.addItems(['Ctrl+Alt+Space', 'Ctrl+Shift+Space', 'Ctrl+Space', 'Alt+Space', 'Ctrl+Alt+V', 'Ctrl+Shift+V', 'Ctrl+F8'])
        hotkey.setCurrentText(self.config['hotkey'])
        provider=QComboBox();provider.addItem('Whisper · Local', 'local');provider.addItem('Gemini 2.5 Flash · Online', 'gemini')
        provider.setCurrentIndex(max(0,provider.findData(self.config.get('provider','local'))))
        consent=QCheckBox('Allow audio uploads to Google')
        consent.setToolTip('Internet required. Google API charges may apply.')
        consent.setChecked(self.config.get('cloud_consent',False))
        api_key=QLineEdit();api_key.setEchoMode(QLineEdit.EchoMode.Password)
        api_key.setMaxLength(512)
        api_key.setPlaceholderText('Key saved; leave blank to keep' if self.secret_path.exists() else 'Gemini API key')
        remove_key=QCheckBox('Delete saved API key')
        auto_location=QCheckBox('Automatically detect weather location')
        auto_location.setChecked(self.config.get('weather_auto_location', True))
        auto_location.setToolTip('Uses Windows Location only when you ask for weather. Falls back to the saved city.')
        weather_location=QLineEdit(self.config.get('weather_location', 'Đà Nẵng'))
        weather_location.setMaxLength(100)
        weather_location.setPlaceholderText('Đà Nẵng')
        def provider_changed():
            online=provider.currentData()=='gemini'
            consent.setEnabled(online)
            api_key.setEnabled(online)
        provider.currentIndexChanged.connect(provider_changed)
        provider_changed()
        status=QLabel();status.setWordWrap(True)
        def update_status(_message=None):
            status.setText('Status: '+self.state.replace('_',' ').title())
        update_status()
        self.changed.connect(update_status)
        diagnostic=QLabel('No test result yet.')
        diagnostic.setWordWrap(True)
        diagnostic.setTextFormat(Qt.TextFormat.PlainText)
        diagnostic.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        def update_diagnostic(_message):
            diagnostic.setText('Test completed. See Voice Debug for recognition details.')
        self.diagnostic_changed.connect(update_diagnostic)
        form.addRow(enabled);form.addRow('Microphone',devices);form.addRow('Hotkey',hotkey);form.addRow(speech)
        form.addRow('Speech-to-Text',provider)
        form.addRow('API key',api_key)
        form.addRow(consent);form.addRow(remove_key)
        form.addRow(auto_location)
        form.addRow('Weather fallback city', weather_location)
        weather_note=QLabel('Weather data: Open-Meteo. Your coordinates or fallback city are sent only when requesting weather.')
        weather_note.setWordWrap(True);weather_note.setObjectName('muted')
        form.addRow(weather_note)
        form.addRow(refresh)
        form.addRow(logging)
        form.addRow(debug_button)
        form.addRow(status)
        form.addRow('Last test', diagnostic)
        test=QPushButton('Hold to test microphone');test.pressed.connect(lambda:self.begin(True));test.released.connect(lambda:self.stop_capture.set())
        form.addRow(test)
        commands=QLabel('Supported commands\n\n'
            'Open This PC: “Mở máy tính”\n'
            'Time: “Mấy giờ rồi”, “Bây giờ là mấy giờ”\n'
            'Date: “Hôm nay là ngày mấy”\n'
            'Weekday: “Hôm nay là thứ mấy”\n'
            'Weather: “Thời tiết hôm nay thế nào”\n'
            'Copy: “Copy”, “Sao chép”\n'
            'Paste: “Paste”, “Dán”, “Dạ”, “Dán nội dung”, “Dán văn bản”\n'
            'Timer: “Hẹn giờ 10 phút”, “Báo thức sau 10 giây” (1 second to 24 hours)\n'
            'Cancel timer: “Hủy hẹn giờ”, “Hủy báo thức”\n'
            'Time remaining: “Còn bao nhiêu phút”, “Hẹn giờ còn bao lâu”\n'
            'Close window: “Đóng cửa sổ”, “Tắt app”\n'
            'Lock screen: “Khóa máy”, “Khóa máy tính”, “Khóa màn hình”')
        commands.setWordWrap(True)
        form.addRow(commands)
        save=QPushButton('Save voice settings')
        if not embedded:outer.addWidget(save)
        def values():
            return (enabled.isChecked(), devices.currentData(), hotkey.currentText(),
                    speech.isChecked(), logging.isChecked(), provider.currentData(),
                    consent.isChecked(), remove_key.isChecked(), api_key.text(),
                    auto_location.isChecked(), weather_location.text())
        original_values = values()
        def apply():
            try:
                if embedded and values() == original_values:return True
                chord = parse_hotkey(hotkey.currentText())[0]
                city = weather_location.text().strip()
                if not city:
                    raise ValueError('Enter a fallback city for weather.')
                if enabled.isChecked() and not devices.model().item(devices.currentIndex()).isEnabled():
                    raise ValueError('Select a connected microphone.')
                if enabled.isChecked() and provider.currentData()=='gemini' and (not consent.isChecked() or remove_key.isChecked()):
                    raise ValueError('Gemini requires an API key and upload consent.')
                if remove_key.isChecked():
                    voice_secret.delete_key(self.secret_path)
                elif api_key.text().strip():
                    voice_secret.save_key(self.secret_path, api_key.text().strip())
                    api_key.clear()
                self.configure(dict(enabled=enabled.isChecked(),device=devices.currentData(),
                                    hotkey=chord,speech=speech.isChecked(),
                                    diagnostic_log=logging.isChecked(),provider=provider.currentData(),
                                    cloud_consent=consent.isChecked(),debug_audio=False,
                                    weather_auto_location=auto_location.isChecked(),
                                    weather_location=city))
                if not embedded:box.accept()
                return True
            except Exception as exc:
                self.message = 'Could not save voice settings: '+str(exc)
                status.setText('Could not save voice settings: '+str(exc))
                return False
        box.apply_voice = apply
        save.clicked.connect(apply)
        def done():
            api_key.clear()
            self.stop_capture.set()
            if not embedded:self.dialog=None
            self.changed.disconnect(update_status)
            self.diagnostic_changed.disconnect(update_diagnostic)
            if not embedded:box.deleteLater()
        if embedded:
            def cleanup():
                self.stop_capture.set()
                self.changed.disconnect(update_status)
                self.diagnostic_changed.disconnect(update_diagnostic)
            box.destroyed.connect(cleanup)
            return box
        box.finished.connect(done)
        self.dialog=box;box.show()

    def close(self):
        self.closed=True
        self.bubble_timer.stop();self.bubble.hide()
        self.timer.stop()
        self.disable()
        self.countdown.cancel()
        self.countdown_label.hide()
        if self.dialog:self.dialog.close()
        if self.debug_dialog:self.debug_dialog.close()
        if self.alarm:self.alarm.close()
        for thread in self.workers:thread.join(timeout=.5)
