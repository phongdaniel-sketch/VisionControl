"""Explicit, bounded, local webcam diagnostic session."""
import argparse
from dataclasses import asdict
import sys
import time

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QSizePolicy

from .diagnostics import DiagnosticInputAdapter, DiagnosticRecorder, frame_record, render_composite
from .monitors import MonitorLayout, ScreenRegion
from .paths import runtime_data_dir
from .runtime import VisionRuntime


class DiagnosticWindow(QWidget):
    closed = Signal()
    def __init__(self, runtime, root=None, *, autostart=True):
        super().__init__()
        self.runtime = runtime
        self.runtime.debug_enabled = True
        self.root = root or runtime_data_dir() / 'captures'
        self.recorder = None
        self.countdown = None
        self.setWindowTitle('VisionControl — Local diagnostics')
        layout = QVBoxLayout(self)
        self.status = QLabel('Đang mở camera ở trạng thái paused…')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.preview = QLabel()
        self.preview.setMinimumSize(320, 140)
        self.preview.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.preview, 1)
        self.start_button = QPushButton('Bắt đầu ghi 30 giây')
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_countdown)
        layout.addWidget(self.start_button)
        self.stop_button = QPushButton('Dừng ghi')
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(lambda: self.stop_recording('user_stopped'))
        layout.addWidget(self.stop_button)
        available = self.screen().availableGeometry()
        self.resize(min(1200, int(available.width() * .9)),
                    min(760, int(available.height() * .9)))
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.tick)
        if autostart:
            QTimer.singleShot(0, self.initialize)

    def initialize(self):
        try:
            self.runtime.start()
            region = ScreenRegion(0, 0, 640, 480, 'Diagnostic area')
            self.runtime.mouse.layout = MonitorLayout([region], 'fixed')
            self.runtime.mouse.target_region = region
            self.runtime.set_paused(True)
            self.status.setText('Paused. Chỉ ghi webcam và vùng thử bên phải; không ghi desktop/âm thanh. '
                                'Con trỏ xanh dùng cùng bộ điều khiển, không tác động chuột thật. '
                                'Bấm bắt đầu khi sẵn sàng; làm theo hướng dẫn dưới video.')
            self.start_button.setEnabled(True)
            self.timer.start()
        except Exception as exc:
            self.fail(exc)

    def start_countdown(self):
        self.countdown = time.monotonic() + 3
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_recording(self, reason='completed'):
        self.countdown = None
        self.runtime.set_paused(True)
        recorder, self.recorder = self.recorder, None
        if recorder is not None:
            recorder.close(reason, self.runtime.adapter.drain())
            self.status.setText(f'Đã lưu {recorder.count} khung hình tại {recorder.directory}. '
                                'Đã paused; bạn có thể đóng cửa sổ và báo tôi kiểm tra.')
        else:
            self.status.setText('Paused — chưa ghi dữ liệu.')
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def tick(self):
        try:
            if self.countdown is not None:
                remaining = self.countdown - time.monotonic()
                self.status.setText(f'Bắt đầu sau {max(0, int(remaining)+1)} giây…')
                if remaining <= 0:
                    self.countdown = None
                    self.recorder = DiagnosticRecorder(self.root, {
                        'profile': asdict(self.runtime.profile),
                        'calibration': asdict(self.runtime.mouse.calibration),
                        'canvas': {'width': 640, 'height': 480},
                    })
                    self.runtime.adapter.drain()
                    self.runtime.set_paused(False)
                    self.status.setText('ĐANG GHI — tự dừng sau 30 giây. Làm theo hướng dẫn dưới video cho chế độ hiện tại.')
            if self.recorder and self.recorder.elapsed >= self.recorder.duration:
                self.stop_recording()
            snapshot = self.runtime.process_frame()
            elapsed = max(0, snapshot.sample_time - self.recorder.started) if self.recorder else 0
            before = time.perf_counter()
            composite = render_composite(snapshot, self.runtime.adapter, elapsed,
                                         self.recorder is not None, self.recorder.count if self.recorder else 0,
                                         self.runtime.profile.pointer_mode,
                                         self.runtime.profile.gesture_v1.get('enabled', False))
            events = self.runtime.adapter.drain()
            if self.recorder:
                record = frame_record(self.runtime, snapshot, events, elapsed)
                record['timings_ms']['composite_render'] = (time.perf_counter() - before) * 1000
                if not self.recorder.append(composite, record):
                    self.stop_recording()
            height, width, _ = composite.shape
            image = QImage(composite.data, width, height, composite.strides[0], QImage.Format.Format_BGR888).copy()
            self.preview.setPixmap(QPixmap.fromImage(image).scaled(
                self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        except Exception as exc:
            self.fail(exc)

    def fail(self, error):
        self.timer.stop()
        try:
            self.stop_recording('error')
        except Exception as cleanup_error:
            error = f'{error}; cleanup: {cleanup_error}'
        finally:
            self.runtime.close()
        self.start_button.setEnabled(False)
        self.status.setText(f'Lỗi chẩn đoán: {error}. Dữ liệu đã ghi trước lỗi nằm tại {self.root}.')

    def closeEvent(self, event):
        self.timer.stop()
        try:
            self.stop_recording('window_closed')
        finally:
            self.runtime.close()
            self.closed.emit()
        event.accept()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--camera-index', type=int, default=0)
    args = parser.parse_args(argv)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    profile = runtime_data_dir() / 'user_profile.json'
    runtime = VisionRuntime(args.camera_index, True, profile if profile.exists() else None,
                            adapter_factory=DiagnosticInputAdapter)
    window = DiagnosticWindow(runtime)
    window.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
