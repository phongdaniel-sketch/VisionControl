import argparse
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QIcon, QImage, QKeyEvent, QPixmap, QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QVBoxLayout, QWidget, QComboBox,
)

from .paths import resource_root
from .runtime import VisionRuntime
from .settings import EDITABLE_GESTURES, load_desktop_settings
from .settings_ui import APP_SETTINGS, USER_PROFILE, SettingsWindow
from .startup import StartupScreen
from .ui_theme import APP_STYLE, humanize
from .controller_labels import POSE_HELP, display_name, mouse_guide


ROOT = resource_root()


class ControllerWindow(QMainWindow):
    def __init__(self, runtime, runtime_factory=VisionRuntime,
                 settings_factory=SettingsWindow):
        super().__init__()
        self.runtime = runtime
        self.runtime_factory = runtime_factory
        self.settings_factory = settings_factory
        self.settings_window = None
        self.diagnostic_window = None
        self.frame_error = None
        self.closing = False
        self.last_frame_time = None
        self.last_status_time = 0.
        self.smoothed_fps = 0.0
        self.capture_deadline = None
        self.calibration_feedback = ""
        self.setWindowTitle("VisionControl")
        self.resize(1280, 780)
        self.setMinimumSize(960, 640)
        icon = QIcon(str(ROOT / "docs" / "Vision Control logo.png"))
        self.setWindowIcon(icon)
        self.setStyleSheet(APP_STYLE)
        self._build_ui()
        self._apply_preview_settings()
        self._refresh_static_runtime_labels()
        self._update_pause_button()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self._process_frame)
        self.timer.start(16)
        self.shortcuts = []
        for key, callback in [('C', self.start_calibration), ('Space', self.space_action),
                              ('R', self.cancel_calibration), ('P', self.toggle_pause)]:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setAutoRepeat(False)
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)

    def _build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(14, 10, 14, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        logo = QLabel()
        source = QPixmap(str(ROOT / "docs" / "Vision Control logo.png"))
        logo.setPixmap(source.scaled(42, 42, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation))
        brand = QLabel("VISION CONTROL")
        brand.setObjectName("brand")
        self.tracking_label = QLabel("● TRACKING")
        self.tracking_label.setStyleSheet("color: #59d36b; font-weight: 700")
        self.fps_label = QLabel("Processing · -- FPS")
        self.fps_label.setObjectName("muted")
        self.fps_label.setToolTip(
            "Measured completed tracking/render cycles, smoothed for readability")
        header.addWidget(logo)
        header.addWidget(brand)
        header.addStretch()
        header.addWidget(self.tracking_label)
        header.addSpacing(18)
        header.addWidget(self.fps_label)
        layout.addLayout(header)
        debug_row = QHBoxLayout()
        self.calibration_view_button = QPushButton('Show calibration area')
        self.calibration_view_button.setCheckable(True)
        self.calibration_view_button.setToolTip('Preview the saved mapping area; does not change calibration.')
        self.debug_button = QPushButton('Debug recording')
        self.debug_button.setEnabled(False)
        self.debug_button.clicked.connect(self.open_diagnostics)
        self.debug_toggle = QPushButton('Debug: Off')
        self.debug_toggle.setCheckable(True)
        self.debug_toggle.toggled.connect(self.toggle_debug)
        self.skeleton_toggle = QPushButton('Skeleton: On')
        self.skeleton_toggle.setCheckable(True)
        self.skeleton_toggle.setChecked(True)
        self.skeleton_toggle.toggled.connect(self.toggle_skeleton)
        self.guide_toggle = QPushButton('Guide: On')
        self.guide_toggle.setCheckable(True)
        self.guide_toggle.setChecked(True)
        self.guide_toggle.toggled.connect(self.toggle_guide)
        self.timing_label = QLabel('')
        self.timing_label.setObjectName('muted')
        self.timing_label.hide()
        debug_row.addWidget(self.calibration_view_button)
        for control in (self.skeleton_toggle, self.guide_toggle, self.debug_button, self.debug_toggle):
            control.hide()
        debug_row.addStretch()
        layout.addLayout(debug_row)
        layout.addWidget(self.timing_label)

        content = QHBoxLayout()
        content.setSpacing(10)
        left_card, left = self._card("STATUS", 235)
        self.status_mode = self._status_row(left, "Controller", "PAUSED")
        self.status_hand = self._status_row(left, "Mouse hand", "--")
        self.status_gesture = self._status_row(left, "Mouse pose", "--")
        self.status_action = self._status_row(left, "Mouse action", "--")
        left.addSpacing(8)
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #253249")
        left.addWidget(divider)
        self.status_keyboard = self._status_row(left, "Keyboard", "DISARMED")
        self.status_keyboard_pose = self._status_row(left, "Key pose", "--")
        self.status_monitor = self._status_row(left, "Display", "--")
        left.addStretch()
        hint = QLabel("P Pause · C Calibrate\nEsc Exit")
        hint.setObjectName("muted")
        left.addWidget(hint)
        content.addWidget(left_card)

        camera_card = QFrame()
        camera_card.setObjectName("card")
        camera_layout = QVBoxLayout(camera_card)
        camera_layout.setContentsMargins(2, 2, 2, 10)
        camera_layout.setSpacing(7)
        self.camera_label = QLabel("Initializing local camera…")
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setMinimumSize(560, 420)
        self.camera_label.setStyleSheet(
            "background: #02050a; border-radius: 10px; color: #718096")
        self.gesture_badge = QLabel("PAUSED · Ready")
        self.gesture_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gesture_badge.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #55a7ff")
        self.help_label = QLabel("")
        self.help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.help_label.setStyleSheet("color: #ff9b70")
        self.help_label.setWordWrap(True)
        camera_layout.addWidget(self.camera_label, 1)
        camera_layout.addWidget(self.gesture_badge)
        camera_layout.addWidget(self.help_label)
        self.calibration_panel = QWidget()
        calibration_layout = QVBoxLayout(self.calibration_panel)
        self.calibration_instruction = QLabel()
        self.calibration_instruction.setWordWrap(True)
        self.calibration_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.calibration_instruction.setStyleSheet("color: #ffbc75; font-size: 14px")
        calibration_layout.addWidget(self.calibration_instruction)
        capture_row = QHBoxLayout()
        self.capture_button = QPushButton("Capture in 3 seconds")
        self.capture_button.clicked.connect(self.schedule_capture)
        self.cancel_calibration_button = QPushButton("Cancel calibration")
        self.cancel_calibration_button.clicked.connect(self.cancel_calibration)
        capture_row.addWidget(self.capture_button)
        capture_row.addWidget(self.cancel_calibration_button)
        calibration_layout.addLayout(capture_row)
        camera_layout.addWidget(self.calibration_panel)
        self.calibration_panel.hide()
        content.addWidget(camera_card, 1)

        guide_card, guide = self._card("GESTURE GUIDE", 260)
        self.guide_card = guide_card
        self.guide_selector = QComboBox()
        self.guide_selector.addItems(["Mouse hand", "Keyboard hand"])
        self.guide_selector.currentIndexChanged.connect(self._refresh_static_runtime_labels)
        guide.addWidget(self.guide_selector)
        self.guide_grid = QGridLayout()
        self.guide_grid.setSpacing(8)
        guide.addLayout(self.guide_grid)
        self.guide_note = QLabel()
        self.guide_note.setObjectName("muted")
        self.guide_note.setWordWrap(True)
        guide.addWidget(self.guide_note)
        guide.addStretch()
        content.addWidget(guide_card)
        layout.addLayout(content, 1)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        self.pause_button = QPushButton("Pause")
        self.pause_button.setObjectName("danger")
        self.pause_button.clicked.connect(self.toggle_pause)
        self.pause_button.setToolTip('Space or P: Pause/Resume while this window is focused. During calibration, Space captures a boundary.')
        self.pause_button.setMinimumWidth(190)
        self.mouse_button = QPushButton("Mouse · Active")
        self.mouse_button.setEnabled(False)
        self.keyboard_button = QPushButton("Keyboard · DISARMED")
        self.keyboard_button.setEnabled(False)
        self.voice_button = QPushButton("Voice · Coming soon")
        self.voice_button.setEnabled(False)
        self.voice_button.setToolTip("Voice control is planned for a future release")
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.open_settings)
        self.calibrate_button = QPushButton("Calibrate")
        self.calibrate_button.clicked.connect(self.start_calibration)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.mouse_button, 1)
        controls.addWidget(self.keyboard_button, 1)
        controls.addWidget(self.voice_button, 1)
        controls.addWidget(self.calibrate_button)
        controls.addWidget(self.settings_button, 1)
        layout.addLayout(controls)
        self.setCentralWidget(root)

    @staticmethod
    def _card(title, width):
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(width)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 11px; font-weight: 700; color: #aeb8c8")
        layout.addWidget(heading)
        return card, layout

    @staticmethod
    def _status_row(layout, name, value):
        row = QHBoxLayout()
        label = QLabel(name)
        label.setObjectName("muted")
        metric = QLabel(value)
        metric.setObjectName("metric")
        metric.setWordWrap(True)
        metric.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(label)
        row.addWidget(metric, 1)
        layout.addLayout(row)
        return metric

    def _refresh_static_runtime_labels(self):
        profile = self.runtime.profile
        self.status_hand.setText(profile.mouse_hand)
        self.guide_selector.setItemText(0, f"Mouse hand · {profile.mouse_hand}")
        self.guide_selector.setItemText(1, f"Keyboard hand · {profile.keyboard_hand}")
        while self.guide_grid.count():
            item = self.guide_grid.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        if self.guide_selector.currentIndex() == 0:
            entries = mouse_guide(profile)
            self.guide_note.setText(
                "Clicks: lock first, curl → straighten.\nFist + thumb tucked: stop."
                if profile.pointer_mode == 'thumb_lock' else
                "Keep the hand visible. Hold a pinch to drag; open it to release. "
                "Edit actions in Settings → Gestures → Mouse hand.")
        else:
            entries = []
            for gesture in EDITABLE_GESTURES:
                binding = profile.bindings.get(gesture)
                action = (f"{'Hold' if binding.action_type == 'hold' else 'Press once'}: "
                          f"{'+'.join(binding.keys).upper()}" if binding else "Disabled")
                entries.append((humanize(gesture), f"{POSE_HELP[gesture]}\n{action}"))
            self.guide_note.setText(
                "Shortcuts work while ACTIVE. Pause stops input. "
                "Fist no longer toggles keyboard control.")
        if profile.gesture_v1.get('enabled'):
            cfg = profile.gesture_v1
            if self.guide_selector.currentIndex() == 0:
                palm_mode = profile.pointer_mode == 'palm'
                entries = [('Move' if palm_mode else 'Move / lock',
                            'Follow palm; open thumb does not lock' if palm_mode else 'Thumb tucked / thumb open'),
                           ('Click with thumb open' if palm_mode else 'Click while locked', 'Curl → extend: index = left; middle = middle; both = right'),
                           ('Drag', 'Apart → pinch; move palm; apart to drop')]
                if cfg['scroll']:
                    entries.append(('Scroll', 'Thumb open, four fingers together; move hand.'))
                if cfg['zoom']:
                    entries.append(('Zoom', 'Spread → gather: in; gather → spread: out.'))
                if cfg['volume']:
                    entries.append(('Volume', 'Fingers toward camera; rotate clockwise: up.'))
                assigned = [name.replace('_', ' ') for name, action in cfg['symbols'].items() if action]
                self.guide_note.setText(('Thumb open enables clicks; palm keeps moving. ' if palm_mode else 'Clicks require lock. ') + ('Symbols: ' + ', '.join(assigned) if assigned else 'Assign symbols/corners in Gestures Settings.'))
            else:
                entries = [('Ctrl', 'Hold fist'), ('Shift', 'Five fingers straight and together'),
                           ('Alt', 'Thumb + index touching')]
                entries += [(f'{n} fingers', binding['keys'].upper()) for n, binding in cfg['bindings'].items()]
                self.guide_note.setText(f"Hold modifiers {cfg['modifier_seconds']:g}s. Release pose to release key. Second hand can be disabled in Settings.")
        for index, (title, action) in enumerate(entries):
            tile = QFrame()
            tile.setObjectName("card")
            tile_layout = QVBoxLayout(tile)
            tile_layout.setContentsMargins(6, 5, 6, 5)
            tile_layout.setSpacing(3)
            gesture_name = QLabel(title)
            gesture_name.setWordWrap(True)
            gesture_name.setStyleSheet("font-size: 12px; font-weight: 600")
            tile_layout.addWidget(gesture_name)
            detail = QLabel(action)
            detail.setObjectName("muted")
            detail.setWordWrap(True)
            tile_layout.addWidget(detail)
            self.guide_grid.addWidget(tile, index, 0)

    def _process_frame(self):
        try:
            snapshot = self.runtime.process_frame()
            if hasattr(self.runtime,'cursor_tick'):self.runtime.cursor_tick()
            if snapshot is None:return
            frame = snapshot.frame
            if self.calibration_view_button.isChecked():
                from .overlay import Overlay
                import cv2
                frame = Overlay(cv2).draw_calibration(frame.copy(), self.runtime.mouse.calibration)
            self._render_frame(frame)
            if time.monotonic()-self.last_status_time >= .1 or self.runtime.calibration_session.active:
                self._render_status(snapshot)
                self.last_status_time = time.monotonic()
        except Exception as exc:
            self.show_runtime_error(exc)

    def show_runtime_error(self, exc):
        self.timer.stop()
        self.runtime.set_paused(True)
        self.runtime.close()
        self.frame_error = str(exc)
        self.camera_label.clear()
        self.camera_label.setText("Camera processing stopped safely")
        self.status_mode.setText("ERROR · PAUSED")
        self.status_action.setText("Released")
        self.status_keyboard.setText("DISARMED")
        self.tracking_label.setText("○ TRACKING · STOPPED")
        self.tracking_label.setStyleSheet("color: #ff9b70; font-weight: 700")
        self.help_label.setText(
            f"{exc}\nCheck camera access and device index, then open Settings and Save to retry.")
        self.pause_button.setText("Paused safely")
        self.pause_button.setEnabled(False)
        self.capture_deadline = None
        self.calibration_panel.hide()
        self.calibrate_button.setEnabled(False)
        QMessageBox.critical(
            self, "VisionControl paused safely",
            f"Camera processing could not continue, but the app will remain open.\n\n"
            f"{exc}\n\nAll mouse buttons and keyboard keys were released. "
            "Allow Camera access if requested, then open Settings and Save to retry.")

    def _render_frame(self, frame):
        height, width, channels = frame.shape
        image = QImage(frame.data, width, height, channels * width,
                       QImage.Format.Format_BGR888).copy()
        pixmap = QPixmap.fromImage(image).scaled(
            self.camera_label.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        self.camera_label.setPixmap(pixmap)
        now = time.monotonic()
        if self.last_frame_time is not None:
            instantaneous = 1.0 / max(now - self.last_frame_time, .001)
            self.smoothed_fps = (instantaneous if self.smoothed_fps == 0 else
                                 self.smoothed_fps * .9 + instantaneous * .1)
            self.fps_label.setText(f"Processing · {self.smoothed_fps:.0f} FPS")
        self.last_frame_time = now

    def _render_status(self, snapshot):
        timings = getattr(snapshot, 'timings_ms', {})
        self.timing_label.setText(' · '.join(
            f'{name}: {timings[key]:.0f} ms' for key, name in
            [('camera_read', 'Camera read'), ('tracking', 'Tracking'),
             ('result_age', 'Frame age'), ('runtime_total', 'Stage total')]
            if key in timings))
        mode = "PAUSED" if snapshot.paused else "ACTIVE"
        self.status_mode.setText(mode)
        self.status_hand.setText(f"{snapshot.mouse_role} · {'Seen' if snapshot.mouse_found else 'Missing'}")
        self.status_gesture.setText(humanize(getattr(snapshot, 'mouse_pose', 'none')))
        self.status_action.setText('Input paused' if snapshot.paused else
                                   snapshot.mouse_status.replace('_', ' ').title())
        keyboard_status = 'Paused' if snapshot.paused else ('Active' if snapshot.keyboard_found else 'No hand')
        if self.runtime.profile.gesture_v1.get('enabled') and not snapshot.paused:
            keyboard_status = snapshot.keyboard_state
        self.status_keyboard.setText(keyboard_status)
        self.status_keyboard_pose.setText(humanize(getattr(snapshot, 'keyboard_pose', 'none')))
        self.status_keyboard_pose.setToolTip(f"Detected pose on the {snapshot.keyboard_role.lower()} hand")
        self.status_monitor.setText(display_name(snapshot.monitor_name))
        self.status_monitor.setToolTip(f"{self.runtime.profile.monitor_mode.title()} mode · {snapshot.monitor_name}")
        mouse_found = "Detected" if snapshot.mouse_found else "Not detected"
        self.mouse_button.setText(f"Mouse · {mouse_found}")
        self.keyboard_button.setText(f"Keyboard · {keyboard_status}")
        progress = (f" · {int(snapshot.arming_progress * 100)}%"
                    if snapshot.arming_progress else "")
        self.gesture_badge.setText('PAUSED · Press Resume to control' if snapshot.paused else
                                  f"ACTIVE · Mouse: {humanize(getattr(snapshot, 'mouse_pose', 'none'))}{progress}")
        self.help_label.setText(self.calibration_feedback or snapshot.help_text)
        self.tracking_label.setText(
            "● TRACKING" if snapshot.hands else "○ TRACKING · NO HANDS")
        self.tracking_label.setStyleSheet(
            "color: #59d36b; font-weight: 700" if snapshot.hands else
            "color: #f0a54a; font-weight: 700")
        self._update_pause_button()
        self._update_calibration(snapshot)

    def _update_pause_button(self):
        desired = "Resume" if self.runtime.paused else "Pause"
        if self.pause_button.text() == desired:
            return
        if self.runtime.paused:
            self.pause_button.setText("Resume")
            self.pause_button.setObjectName("primary")
        else:
            self.pause_button.setText("Pause")
            self.pause_button.setObjectName("danger")
        self.pause_button.style().unpolish(self.pause_button)
        self.pause_button.style().polish(self.pause_button)

    def toggle_pause(self):
        if (self.frame_error is not None or self.settings_window is not None or
                not self.runtime.started or self.runtime.calibration_session.active):
            return
        self.runtime.toggle_paused()
        self._update_pause_button()

    def space_action(self):
        if self.runtime.calibration_session.active:
            self.capture_calibration()
        else:
            self.toggle_pause()

    def start_calibration(self):
        if not getattr(self.runtime, 'started', False) or self.settings_window is not None:
            return
        self.capture_deadline = None
        self.calibration_feedback = ''
        self.runtime.start_calibration()
        self._update_pause_button()
        self._update_calibration(self.runtime.last_snapshot)

    def schedule_capture(self):
        session = self.runtime.calibration_session
        if session.active and self.capture_deadline is None:
            self.calibration_feedback = ''
            self.capture_deadline = time.monotonic() + 3

    def capture_calibration(self):
        session = getattr(self.runtime, 'calibration_session', None)
        if session is None or not session.active:
            return
        self.capture_deadline = None
        before = session.index
        try:
            complete = self.runtime.capture_calibration()
            if complete:
                self.calibration_feedback = 'Calibration saved locally. Ready for next launch. Press Resume to test.'
            elif session.index == before:
                self.calibration_feedback = ('Mouse hand not detected clearly. Keep the whole hand visible; '
                                             'check Mouse hand / Swap hands in Settings if needed.')
            else:
                self.calibration_feedback = 'Boundary captured. Move to the next edge.'
        except Exception as exc:
            self.calibration_feedback = f'Not saved: {exc} Retry this step, or Cancel to keep the previous calibration.'
        self.help_label.setText(self.calibration_feedback)
        self._update_calibration(self.runtime.last_snapshot)

    def cancel_calibration(self):
        session = getattr(self.runtime, 'calibration_session', None)
        if session is None or not session.active:
            return
        self.capture_deadline = None
        self.runtime.cancel_calibration()
        self.calibration_feedback = 'Calibration cancelled. Previous calibration kept. Controller stays paused.'
        self.help_label.setText(self.calibration_feedback)
        self._update_calibration(self.runtime.last_snapshot)

    def _update_calibration(self, snapshot):
        session = getattr(self.runtime, 'calibration_session', None)
        active = session is not None and session.active
        self.calibration_panel.setVisible(active)
        self.calibrate_button.setEnabled(not active and self.frame_error is None)
        self.pause_button.setEnabled(not active and self.frame_error is None)
        if not active:
            return
        self.status_mode.setText('CALIBRATING')
        self.gesture_badge.setText('CALIBRATION · Mouse and keyboard input paused')
        found = snapshot is not None and snapshot.mouse_found
        directions = {'left': 'LEFT ←', 'right': 'RIGHT →', 'top': 'TOP ↑', 'bottom': 'BOTTOM ↓'}
        instruction = (f'Step {session.index + 1}/4 · {directions[session.stage]} edge of the preview\n'
                       f'Move your {self.runtime.profile.mouse_hand.lower()} {"palm center" if self.runtime.profile.pointer_mode == "palm" else "index fingertip"} to a comfortable '
                       'boundary. Keep the hand visible. Press Space, or use the countdown button.')
        if not found:
            instruction += '\nMouse hand missing — check the selected hand and camera view.'
        self.calibration_instruction.setText(instruction)
        self.capture_button.setEnabled(found and self.capture_deadline is None)
        if self.capture_deadline is not None:
            if not found:
                self.capture_deadline = None
                self.calibration_feedback = 'Countdown cancelled: mouse hand lost. Show the hand and try again.'
                self.help_label.setText(self.calibration_feedback)
            else:
                remaining = self.capture_deadline - time.monotonic()
                if remaining <= 0:
                    self.capture_calibration()
                    return
                self.capture_button.setText(f'Hold at this edge · {remaining:.1f}s')
                return
        self.capture_button.setText('Capture in 3 seconds')

    def open_settings(self):
        if self.diagnostic_window is not None:
            return
        self.cancel_calibration()
        self.runtime.set_paused(True)
        self._update_pause_button()
        self.timer.stop()
        if self.settings_window is not None:
            self.settings_window.raise_()
            self.settings_window.activateWindow()
            return
        self.settings_window = self.settings_factory(parent=self)
        self.settings_window.settings_saved.connect(self._reload_after_settings)
        if hasattr(self.settings_window, 'debug_recording_requested'):
            self.settings_window.debug_recording_requested.connect(self._record_from_settings)
        self.settings_window.destroyed.connect(self._settings_closed)
        self.settings_window.show()

    def _record_from_settings(self):
        self.settings_window = None
        QTimer.singleShot(0, self.open_diagnostics)

    def _apply_preview_settings(self, debug=False):
        desktop = load_desktop_settings(APP_SETTINGS)
        self.skeleton_toggle.setChecked(desktop.show_skeleton)
        self.guide_toggle.setChecked(desktop.show_guide)
        self.debug_toggle.setChecked(debug)
        self.toggle_skeleton(desktop.show_skeleton)
        self.toggle_guide(desktop.show_guide)
        self.toggle_debug(debug)

    def open_diagnostics(self):
        if self.diagnostic_window is not None or self.settings_window is not None:
            return
        from .diagnostics import DiagnosticInputAdapter
        from .diagnostics_ui import DiagnosticWindow
        self.cancel_calibration()
        self.timer.stop()
        self.runtime.set_paused(True)
        self.runtime.close()
        self._update_pause_button()
        try:
            diagnostic_runtime = VisionRuntime(self.runtime.camera_index, True,
                self.runtime.profile_path, adapter_factory=DiagnosticInputAdapter)
            self.diagnostic_window = DiagnosticWindow(diagnostic_runtime)
            self.diagnostic_window.closed.connect(self._diagnostics_closed)
            self.diagnostic_window.show()
            self.help_label.setText('Controller paused. Close Debug recording to return here.')
        except Exception:
            self._diagnostics_closed()
            raise

    def _diagnostics_closed(self):
        self.diagnostic_window = None
        if self.closing:
            return
        try:
            self.runtime.set_paused(True)
            self.runtime.start()
            self._refresh_static_runtime_labels()
            self.frame_error = None
            self.pause_button.setEnabled(True)
            self.last_frame_time = None
            self.smoothed_fps = 0
            self._update_pause_button()
            self.timer.start(16)
        except Exception as exc:
            self.show_runtime_error(exc)

    def toggle_skeleton(self, enabled):
        self.runtime.landmarks_enabled = enabled
        self.skeleton_toggle.setText('Skeleton: On' if enabled else 'Skeleton: Off')

    def toggle_guide(self, enabled):
        self.guide_card.setVisible(enabled)
        self.guide_toggle.setText('Guide: On' if enabled else 'Guide: Off')

    def toggle_debug(self, enabled):
        self.runtime.debug_enabled = enabled
        self.debug_toggle.setText('Debug: On' if enabled else 'Debug: Off')
        self.debug_button.setEnabled(enabled)
        self.timing_label.setVisible(enabled)
        if not enabled and self.diagnostic_window is not None:
            self.diagnostic_window.close()

    def _settings_closed(self):
        self.settings_window = None
        if not self.closing and self.runtime.started and self.diagnostic_window is None:
            self.last_frame_time = None
            self.smoothed_fps = 0.0
            self.fps_label.setText("Processing · -- FPS")
            self.timer.start(16)

    def _reload_after_settings(self):
        debug = bool(getattr(self.settings_window, 'debug_view', self.debug_toggle).isChecked())
        open_recording = bool(getattr(self.settings_window, 'open_recording_after_save', False))
        self.timer.stop()
        self.runtime.set_paused(True)
        self.runtime.close()
        desktop = load_desktop_settings(APP_SETTINGS)
        profile_path = USER_PROFILE if USER_PROFILE.exists() else ROOT / 'config' / 'gesture_v1_profile.json'
        try:
            self.runtime = self.runtime_factory(
                desktop.camera_index, True, profile_path)
            if isinstance(self.runtime, VisionRuntime):
                self.runtime.async_mode = True
            self._apply_preview_settings(debug)
            if open_recording:
                return  # Recorder opens the camera; avoid opening it twice.
            self.runtime.start()
            self.frame_error = None
            self.last_frame_time = None
            self.smoothed_fps = 0.0
            self.fps_label.setText("Processing · -- FPS")
            self._refresh_static_runtime_labels()
            self.pause_button.setEnabled(True)
            self.calibrate_button.setEnabled(True)
            self._update_pause_button()
            self.timer.start(16)
        except Exception as exc:
            self.show_runtime_error(exc)

    def keyPressEvent(self, event: QKeyEvent):
        if event.isAutoRepeat():
            return
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.close()
        elif key == Qt.Key.Key_P:
            self.toggle_pause()
        elif key == Qt.Key.Key_C:
            self.start_calibration()
        elif key == Qt.Key.Key_Space:
            self.space_action()
        elif key == Qt.Key.Key_R:
            self.cancel_calibration()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent):
        self.closing = True
        self.timer.stop()
        if self.diagnostic_window is not None:
            self.diagnostic_window.close()
        self.runtime.close()
        if self.settings_window is not None:
            self.settings_window.close()
        event.accept()
        app = QApplication.instance()
        if app is not None:
            QTimer.singleShot(0, app.quit)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="VisionControl desktop controller")
    parser.add_argument("--camera-index", type=int)
    parser.add_argument("--start-paused", action="store_true")
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--quit-after", type=float, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    desktop = load_desktop_settings(APP_SETTINGS)
    camera_index = desktop.camera_index if args.camera_index is None else args.camera_index
    start_paused = desktop.start_paused or args.start_paused
    profile_path = args.profile or (USER_PROFILE if USER_PROFILE.exists() else ROOT / 'config' / 'gesture_v1_profile.json')

    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("VisionControl")
    # OpenCV owns the temporary startup windows. Keep Qt alive while those
    # windows are destroyed and the Controller becomes the primary window.
    app.setQuitOnLastWindowClosed(False)
    app.setStyleSheet(APP_STYLE)
    icon = QIcon(str(ROOT / "docs" / "Vision Control logo.png"))
    app.setWindowIcon(icon)
    runtime = VisionRuntime(camera_index, start_paused, profile_path, async_mode=True)
    window = None
    try:
        import cv2
        startup = StartupScreen(cv2, ROOT / "docs" / "Splash Screen.png",
                                ROOT / "docs" / "Loading Screen.png")
        startup.show_splash(1000)
        runtime.start(lambda value, message:
                      startup.show_loading(value, message,
                                           250 if value >= 1 else 1))
        cv2.destroyAllWindows()
        app.processEvents()
        window = ControllerWindow(runtime)
        window.show()
        app.processEvents()
        if args.quit_after is not None:
            QTimer.singleShot(max(1, int(args.quit_after * 1000)), window.close)
        return app.exec()
    except Exception as exc:
        runtime.close()
        try:
            import cv2
            cv2.destroyAllWindows()
        except Exception:
            pass
        if runtime.profile is None:
            QMessageBox.critical(None, "VisionControl could not start", str(exc))
            return 1
        window = ControllerWindow(runtime)
        window.show()
        app.processEvents()
        QTimer.singleShot(0, lambda error=exc: window.show_runtime_error(error))
        if args.quit_after is not None:
            QTimer.singleShot(max(1, int(args.quit_after * 1000)), window.close)
        return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
