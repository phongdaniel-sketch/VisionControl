"""Guided capture, per-pose review and inert rehearsal on the existing camera."""
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QMessageBox,
                              QProgressBar, QPushButton, QScrollArea, QVBoxLayout, QWidget)

from .pose_calibration import PoseCapture, PosePreview, STAGES, fit, measure
from .pose_guide import GUIDE, BUTTON_NAMES, FINGER_NAMES, PoseExample, capture_error, fit_error
from .roles import assign_roles
from .types import HandsFrame


class PoseCalibrationDialog(QDialog):
    def __init__(self, runtime, parent=None):
        super().__init__(parent)
        self.runtime = runtime
        self.capture = PoseCapture()
        self.rehearsal = None
        self.review_stage = None
        self.outcome = '\u0110\u00e3 h\u1ee7y. Gi\u1eef nguy\u00ean c\u1ea5u h\u00ecnh t\u01b0 th\u1ebf c\u0169; \u0111i\u1ec1u khi\u1ec3n v\u1eabn t\u1ea1m d\u1eebng.'
        self.setWindowTitle('Calibrate - Hi\u1ec7u ch\u1ec9nh t\u01b0 th\u1ebf')
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.resize(820, 730)
        self.setMinimumSize(640, 580)
        root = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setSpacing(8)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)
        self.title = QLabel()
        self.title.setWordWrap(True)
        self.title.setStyleSheet('font-size: 18px; font-weight: 600;')
        layout.addWidget(self.title)
        role = 'ph\u1ea3i' if runtime.profile.mouse_hand == 'Right' else 'tr\u00e1i'
        self.safety = QLabel(f'Tay \u0111i\u1ec1u khi\u1ec3n: {role} | Chu\u1ed9t v\u00e0 b\u00e0n ph\u00edm \u0111ang t\u1ea1m d\u1eebng')
        self.safety.setWordWrap(True)
        layout.addWidget(self.safety)
        self.preparation = QLabel('\u0110\u01b0a \u0111\u1ee7 b\u00e0n tay v\u00e0o camera, l\u00f2ng b\u00e0n tay h\u01b0\u1edbng v\u1ec1 camera. '
            '\u0110\u1ec3 ng\u00f3n \u00e1p \u00fat v\u00e0 \u00fat tho\u1ea3i m\u00e1i. H\u00ecnh b\u00ean tr\u00e1i l\u00e0 m\u1eabu minh h\u1ecda, kh\u00f4ng ph\u1ea3i tay \u0111\u01b0\u1ee3c nh\u1eadn di\u1ec7n.')
        self.preparation.setWordWrap(True)
        layout.addWidget(self.preparation)
        images = QHBoxLayout()
        example_column = QVBoxLayout()
        example_column.addWidget(QLabel('T\u01b0 th\u1ebf m\u1eabu'))
        self.example = PoseExample()
        example_column.addWidget(self.example, alignment=Qt.AlignmentFlag.AlignCenter)
        images.addLayout(example_column)
        camera_column = QVBoxLayout()
        self.tracking = QLabel('Camera tr\u1ef1c ti\u1ebfp - \u0111ang ch\u1edd tay')
        self.tracking.setWordWrap(True)
        camera_column.addWidget(self.tracking)
        self.preview = QLabel('\u0110ang ch\u1edd camera...')
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setFixedHeight(210)
        self.preview.setMinimumWidth(240)
        camera_column.addWidget(self.preview)
        images.addLayout(camera_column, 1)
        layout.addLayout(images)
        self.instruction = QLabel()
        self.instruction.setWordWrap(True)
        layout.addWidget(self.instruction)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        self.feedback = QLabel()
        self.feedback.setWordWrap(True)
        self.feedback.setMinimumHeight(34)
        layout.addWidget(self.feedback)
        self.result = QLabel()
        self.result.setWordWrap(True)
        layout.addWidget(self.result)
        layout.addStretch()
        actions = QHBoxLayout()
        self.capture_button = QPushButton('Thu m\u1eabu (sau 3 gi\u00e2y)')
        self.capture_button.clicked.connect(self.begin_capture)
        actions.addWidget(self.capture_button)
        self.retry_button = QPushButton('Thu l\u1ea1i b\u01b0\u1edbc n\u00e0y')
        self.retry_button.clicked.connect(self.retry_step)
        actions.addWidget(self.retry_button)
        self.next_button = QPushButton('Ti\u1ebfp t\u1ee5c')
        self.next_button.clicked.connect(self.next_step)
        actions.addWidget(self.next_button)
        root.addLayout(actions)
        footer = QHBoxLayout()
        self.restart_button = QPushButton('L\u00e0m l\u1ea1i t\u1eeb \u0111\u1ea7u')
        self.restart_button.clicked.connect(self.restart)
        footer.addWidget(self.restart_button)
        self.reset_button = QPushButton('V\u1ec1 m\u1eb7c \u0111\u1ecbnh')
        self.reset_button.clicked.connect(self.reset_defaults)
        footer.addWidget(self.reset_button)
        footer.addStretch()
        self.cancel_button = QPushButton('H\u1ee7y')
        self.cancel_button.clicked.connect(self.reject)
        footer.addWidget(self.cancel_button)
        self.save_button = QPushButton('L\u01b0u t\u01b0 th\u1ebf')
        self.save_button.setObjectName('primary')
        self.save_button.setStyleSheet('QPushButton:disabled { background: #0a101b; color: #718097; border-color: #26344a; }')
        self.save_button.clicked.connect(self.save)
        self.save_button.setEnabled(False)
        footer.addWidget(self.save_button)
        root.addLayout(footer)
        for button in self.findChildren(QPushButton):
            button.setAutoDefault(False)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)
        self.refresh_stage()

    def refresh_stage(self):
        stage = self.review_stage or self.capture.stage
        self.capture_button.setEnabled(self.review_stage is None and stage is not None and self.capture.deadline is None)
        self.retry_button.setEnabled(self.review_stage is not None)
        self.next_button.setEnabled(self.review_stage is not None)
        self.next_button.setText('Th\u1eed nh\u1eadn di\u1ec7n' if self.review_stage == 'both' else 'Ti\u1ebfp t\u1ee5c')
        if stage is not None:
            number = STAGES.index(stage)+1
            title, lines = GUIDE[stage]
            self.title.setText(f'B\u01b0\u1edbc {number}/5: {title}')
            self.instruction.setText('\n'.join(f'{i}. {line}' for i,line in enumerate(lines,1)))
            self.example.set_stage(stage)
            self.result.setText('\u0110\u00e2y l\u00e0 thu t\u01b0 th\u1ebf t\u0129nh: gi\u1eef nguy\u00ean ng\u00f3n, ch\u01b0a th\u1ef1c hi\u1ec7n \u0111\u1ed9ng t\u00e1c click.')
            if self.review_stage:
                self.feedback.setText('\u0110\u00e3 thu m\u1eabu b\u01b0\u1edbc n\u00e0y. B\u1ea5m Ti\u1ebfp t\u1ee5c \u0111\u1ec3 x\u00e1c nh\u1eadn, ho\u1eb7c Thu l\u1ea1i b\u01b0\u1edbc n\u00e0y.')
        elif self.rehearsal is not None:
            self.title.setText('Th\u1eed nh\u1eadn di\u1ec7n - ch\u01b0a t\u00e1c \u0111\u1ed9ng l\u00ean desktop')
            self.progress.setValue(0)
            self.render_rehearsal(time.monotonic())

    def begin_capture(self):
        if self.capture.stage is None or self.review_stage is not None or self.capture.deadline is not None:
            return
        self.capture.begin(time.monotonic())
        self.progress.setValue(0)
        self.progress.setFormat('%p%')
        self.feedback.setText('B\u1ea1n c\u00f3 3 gi\u00e2y \u0111\u1ec3 r\u1eddi chu\u1ed9t v\u00e0 \u0111\u01b0a tay v\u00e0o t\u01b0 th\u1ebf m\u1eabu.')
        self.refresh_stage()

    def retry_step(self):
        if self.review_stage is None:
            return
        self.capture.samples.pop(self.review_stage)
        self.review_stage = None
        self.progress.setValue(0)
        self.feedback.setText('Chu\u1ea9n b\u1ecb l\u1ea1i t\u01b0 th\u1ebf r\u1ed3i b\u1ea5m Thu m\u1eabu. C\u00e1c b\u01b0\u1edbc tr\u01b0\u1edbc v\u1eabn \u0111\u01b0\u1ee3c gi\u1eef.')
        self.refresh_stage()

    def next_step(self):
        if self.review_stage is None:
            return
        self.review_stage = None
        self.feedback.clear()
        self.progress.setValue(0)
        if self.capture.stage is None:
            try:
                self.rehearsal = PosePreview(fit(self.capture.samples), self.runtime.profile.thresholds)
            except ValueError as exc:
                self.feedback.setText(fit_error(str(exc)))
                self.instruction.setText('B\u1ea5m L\u00e0m l\u1ea1i t\u1eeb \u0111\u1ea7u \u0111\u1ec3 thu b\u1ed9 m\u1eabu m\u1edbi. Ch\u01b0a thay \u0111\u1ed5i c\u1ea5u h\u00ecnh \u0111ang d\u00f9ng.')
                self.result.clear()
        self.refresh_stage()

    def restart(self):
        self.capture = PoseCapture()
        self.rehearsal = None
        self.review_stage = None
        self.save_button.setEnabled(False)
        self.progress.setValue(0)
        self.progress.setFormat('%p%')
        self.feedback.clear()
        self.result.clear()
        self.refresh_stage()

    def render_rehearsal(self, now):
        r = self.rehearsal
        if not r.tucked:
            self.instruction.setText('Th\u1eed 1/4: Thu ng\u00f3n c\u00e1i v\u00e0o l\u00f2ng b\u00e0n tay, v\u1eabn du\u1ed7i ng\u00f3n tr\u1ecf v\u00e0 gi\u1eefa.\n'
                'Gi\u1eef m\u1ed9t nh\u1ecbp \u0111\u1ebfn khi hi\u1ec7n OK. Kh\u00f4ng c\u1ea7n b\u1ea5m n\u00fat Thu m\u1eabu n\u1eefa.')
            self.example.set_stage('tucked')
        elif not r.complete:
            button = next(b for b in ('left','middle','right') if b not in r.seen)
            stage = {'left':'index','middle':'both','right':'right_contact'}[button]
            finger = {'left':'ng\u00f3n tr\u1ecf','middle':'ng\u00f3n tr\u1ecf v\u00e0 ng\u00f3n gi\u1eefa c\u00f9ng l\u00fac','right':''}[button]
            self.instruction.setText(f'Th\u1eed click {BUTTON_NAMES[button]}:\n'
                '1. M\u1edf ng\u00f3n c\u00e1i, du\u1ed7i ng\u00f3n tr\u1ecf v\u00e0 gi\u1eefa; gi\u1eef kho\u1ea3ng 0,2 gi\u00e2y.\n'
                f'2. G\u1eadp {finger}, r\u1ed3i du\u1ed7i tr\u1edf l\u1ea1i trong kho\u1ea3ng 0,8 gi\u00e2y. Gi\u1eef ng\u00f3n c\u00e1i m\u1edf.\n'
                '3. Xem tr\u1ea1ng th\u00e1i OK b\u00ean d\u01b0\u1edbi. Ch\u1ec9 g\u1eadp m\u00e0 ch\u01b0a du\u1ed7i l\u1ea1i th\u00ec ch\u01b0a t\u00ednh l\u00e0 click.')
            self.example.set_stage(stage if .7 <= now % 2 < 1.0 else 'open')
            if button == 'right':
                self.instruction.setText('Th\u1eed click ph\u1ea3i:\n'
                    '1. T\u00e1ch ng\u00f3n c\u00e1i kh\u1ecfi ng\u00f3n tr\u1ecf v\u00e0 ng\u00f3n gi\u1eefa \u0111\u1ec3 chu\u1ea9n b\u1ecb.\n'
                    '2. Ch\u1ea1m \u0111\u1ea7u ng\u00f3n c\u00e1i v\u1edbi \u0111\u1ea7u ng\u00f3n gi\u1eefa. Click \u0111\u01b0\u1ee3c t\u00ednh ngay l\u00fac ch\u1ea1m, kh\u00f4ng c\u1ea7n ch\u1edd th\u1ea3.\n'
                    '3. Gi\u1eef ti\u1ebfp x\u00fac kh\u00f4ng click l\u1eb7p. T\u00e1ch hai ng\u00f3n \u0111\u1ec3 chu\u1ea9n b\u1ecb l\u1ea7n ti\u1ebfp theo; \u0111\u1eebng ch\u1ea1m ng\u00f3n tr\u1ecf.')
                self.example.set_stage('right_contact' if now % 2 >= .7 else 'open')
        else:
            self.instruction.setText('\u0110\u00e3 nh\u1eadn \u0111\u1ee7 ba lo\u1ea1i click v\u00e0 tr\u1ea1ng th\u00e1i thu ng\u00f3n c\u00e1i.\n'
                'B\u1ea5m L\u01b0u t\u01b0 th\u1ebf \u0111\u1ec3 \u00e1p d\u1ee5ng. Sau khi \u0111\u00f3ng c\u1eeda s\u1ed5, b\u1ea5m Start khi b\u1ea1n s\u1eb5n s\u00e0ng \u0111i\u1ec1u khi\u1ec3n.')
            self.example.set_stage('open')
        status = ['Thu ng\u00f3n c\u00e1i: '+('OK' if r.tucked else 'ch\u01b0a th\u1eed')]
        status.extend(f'Click {BUTTON_NAMES[b]}: '+('OK' if b in r.seen else 'ch\u01b0a th\u1eed') for b in ('left','middle','right'))
        self.result.setText(' | '.join(status))
        self.progress.setValue(25*(len(r.seen)+int(r.tucked)))
        self.save_button.setEnabled(r.complete)

    def tick(self):
        if not self.runtime.started or not self.runtime.pose_calibrating:
            self.reject(); return
        parent = self.parent()
        if parent is not None and getattr(parent,'frame_error',None) is not None:
            self.reject(); return
        snapshot = self.runtime.last_snapshot
        now = time.monotonic()
        hand, size, stamp = None, (640,480), 0.
        if snapshot is not None:
            stamp = snapshot.sample_time
            hand, _ = assign_roles(HandsFrame(0,snapshot.hands),self.runtime.profile.mouse_hand,
                                  self.runtime.profile.keyboard_hand,self.runtime.profile.swap_hands)
            if snapshot.frame is not None:
                frame = snapshot.frame
                height, width = frame.shape[:2]
                size = (width,height)
                if 0 <= now-stamp <= .15:
                    rgb = frame[:,:,::-1].copy()
                    image = QImage(rgb.data,width,height,rgb.strides[0],QImage.Format.Format_RGB888).copy()
                    self.preview.setPixmap(QPixmap.fromImage(image).scaled(self.preview.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        fresh = snapshot is not None and 0 <= now-stamp <= .15
        if not fresh:
            self.preview.setText('\u0110ang ch\u1edd khung h\u00ecnh m\u1edbi t\u1eeb camera...')
        found = fresh and measure(hand,size) is not None
        self.tracking.setText('Camera tr\u1ef1c ti\u1ebfp - \u0111\u00e3 th\u1ea5y tay' if found else 'Ch\u01b0a r\u00f5 tay \u0111i\u1ec1u khi\u1ec3n: ki\u1ec3m tra v\u1ecb tr\u00ed tay / Swap hands')
        if self.rehearsal is not None:
            r = self.rehearsal
            buttons = r.update(hand,size,stamp,now)
            if found:
                thumb = FINGER_NAMES[r.candidate.thumb(hand,size)]
                index = FINGER_NAMES[r.candidate.finger(hand,8,size)]
                middle = FINGER_NAMES[r.candidate.finger(hand,12,size)]
                self.feedback.setText(f'\u0110ang nh\u1eadn: c\u00e1i {thumb} | tr\u1ecf {index} | gi\u1eefa {middle}')
            else:
                self.feedback.setText('M\u1ea5t d\u1ea5u tay: \u0111\u1ed9ng t\u00e1c \u0111ang th\u1eed \u0111\u00e3 \u0111\u01b0\u1ee3c \u0111\u1eb7t l\u1ea1i. \u0110\u01b0a tay v\u00e0o r\u1ed3i th\u1eed l\u1ea1i.')
            if buttons:
                self.progress.setFormat('V\u1eeba nh\u1eadn click '+BUTTON_NAMES[buttons[-1]])
            self.render_rehearsal(now)
            return
        deadline = self.capture.deadline
        if deadline is None or self.review_stage is not None:
            return
        stage = self.capture.stage
        done = self.capture.observe(hand,size,stamp,now)
        if done:
            self.review_stage = stage
            self.progress.setValue(100)
            self.refresh_stage()
        elif self.capture.deadline is None:
            self.feedback.setText(capture_error(self.capture.message))
            self.refresh_stage()
        elif now < deadline:
            self.feedback.setText(f'C\u00f2n {max(0,deadline-now):.1f} gi\u00e2y: \u0111\u01b0a tay v\u00e0o t\u01b0 th\u1ebf m\u1eabu.')
        else:
            elapsed = stamp-(self.capture.first_time if self.capture.first_time is not None else stamp)
            self.progress.setValue(min(99,round(elapsed/1.2*100)))
            self.feedback.setText(f'\u0110ang thu {len(self.capture.pending)} khung h\u00ecnh. Gi\u1eef nguy\u00ean t\u01b0 th\u1ebf, ch\u01b0a du\u1ed7i/g\u1eadp th\u00eam.')

    def save(self):
        if self.rehearsal is None or not self.rehearsal.complete:
            return
        try:
            self.runtime.save_pose_calibration(self.rehearsal.candidate)
        except Exception as exc:
            self.feedback.setText(f'Ch\u01b0a l\u01b0u \u0111\u01b0\u1ee3c: {exc}. Th\u1eed L\u01b0u l\u1ea1i ho\u1eb7c H\u1ee7y.')
            return
        self.outcome = '\u0110\u00e3 l\u01b0u t\u01b0 th\u1ebf. \u0110i\u1ec1u khi\u1ec3n v\u1eabn t\u1ea1m d\u1eebng; b\u1ea5m Start khi s\u1eb5n s\u00e0ng.'
        self.accept()

    def reset_defaults(self):
        answer = QMessageBox.question(self,'V\u1ec1 m\u1eb7c \u0111\u1ecbnh',
            'X\u00f3a ng\u01b0\u1ee1ng t\u01b0 th\u1ebf \u0111\u00e3 l\u01b0u cho tay \u0111i\u1ec1u khi\u1ec3n n\u00e0y? V\u00f9ng di chuy\u1ec3n kh\u00f4ng b\u1ecb thay \u0111\u1ed5i.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.runtime.reset_pose_calibration()
        except Exception as exc:
            self.feedback.setText(f'Ch\u01b0a \u0111\u1eb7t l\u1ea1i \u0111\u01b0\u1ee3c: {exc}')
            return
        self.outcome = '\u0110\u00e3 kh\u00f4i ph\u1ee5c ng\u01b0\u1ee1ng m\u1eb7c \u0111\u1ecbnh. \u0110i\u1ec1u khi\u1ec3n v\u1eabn t\u1ea1m d\u1eebng.'
        self.accept()

    def done(self, result):
        self.timer.stop()
        self.runtime.finish_pose_calibration()
        super().done(result)
