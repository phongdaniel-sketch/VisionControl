import argparse
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QIcon, QImage, QKeyEvent, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from .paths import resource_root
from .runtime import VisionRuntime
from .settings import EDITABLE_GESTURES, load_desktop_settings
from .settings_ui import APP_SETTINGS, USER_PROFILE, SettingsWindow
from .startup import StartupScreen
from .ui_theme import APP_STYLE, humanize


ROOT = resource_root()


class ControllerWindow(QMainWindow):
    def __init__(self, runtime, runtime_factory=VisionRuntime,
                 settings_factory=SettingsWindow):
        super().__init__()
        self.runtime = runtime
        self.runtime_factory = runtime_factory
        self.settings_factory = settings_factory
        self.settings_window = None
        self.last_frame_time = None
        self.smoothed_fps = 0.0
        self.setWindowTitle("VisionControl")
        self.resize(1280, 780)
        self.setMinimumSize(960, 640)
        icon = QIcon(str(ROOT / "docs" / "Vision Control logo.png"))
        self.setWindowIcon(icon)
        self.setStyleSheet(APP_STYLE)
        self._build_ui()
        self._refresh_static_runtime_labels()
        self._update_pause_button()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self._process_frame)
        self.timer.start(16)

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
        self.fps_label = QLabel("-- FPS")
        self.fps_label.setObjectName("muted")
        header.addWidget(logo)
        header.addWidget(brand)
        header.addStretch()
        header.addWidget(self.tracking_label)
        header.addSpacing(18)
        header.addWidget(self.fps_label)
        layout.addLayout(header)

        content = QHBoxLayout()
        content.setSpacing(10)
        left_card, left = self._card("STATUS", 210)
        self.status_mode = self._status_row(left, "Controller", "PAUSED")
        self.status_hand = self._status_row(left, "Mouse hand", "--")
        self.status_gesture = self._status_row(left, "Gesture", "--")
        self.status_action = self._status_row(left, "Mouse action", "--")
        left.addSpacing(8)
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #253249")
        left.addWidget(divider)
        self.status_keyboard = self._status_row(left, "Keyboard", "DISARMED")
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
        content.addWidget(camera_card, 1)

        guide_card, guide = self._card("GESTURE GUIDE", 220)
        self.guide_grid = QGridLayout()
        self.guide_grid.setSpacing(8)
        guide.addLayout(self.guide_grid)
        guide.addStretch()
        note = QLabel("Fist is reserved for keyboard arm/disarm")
        note.setObjectName("muted")
        note.setWordWrap(True)
        guide.addWidget(note)
        content.addWidget(guide_card)
        layout.addLayout(content, 1)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        self.pause_button = QPushButton("Pause")
        self.pause_button.setObjectName("danger")
        self.pause_button.clicked.connect(self.toggle_pause)
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
        controls.addWidget(self.pause_button)
        controls.addWidget(self.mouse_button, 1)
        controls.addWidget(self.keyboard_button, 1)
        controls.addWidget(self.voice_button, 1)
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
        metric.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(label)
        row.addWidget(metric, 1)
        layout.addLayout(row)
        return metric

    def _refresh_static_runtime_labels(self):
        profile = self.runtime.profile
        self.status_hand.setText(profile.mouse_hand)
        while self.guide_grid.count():
            item = self.guide_grid.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        for index, gesture in enumerate(EDITABLE_GESTURES):
            binding = profile.bindings.get(gesture)
            action = "Disabled"
            if binding:
                keys = "+".join(binding.keys).upper()
                action = f"{binding.action_type.title()} · {keys}"
            tile = QFrame()
            tile.setObjectName("card")
            tile_layout = QVBoxLayout(tile)
            tile_layout.setContentsMargins(8, 8, 8, 8)
            gesture_name = QLabel(humanize(gesture))
            gesture_name.setWordWrap(True)
            gesture_name.setStyleSheet("font-size: 12px; font-weight: 600")
            tile_layout.addWidget(gesture_name)
            detail = QLabel(action)
            detail.setObjectName("muted")
            detail.setWordWrap(True)
            tile_layout.addWidget(detail)
            self.guide_grid.addWidget(tile, index // 2, index % 2)

    def _process_frame(self):
        try:
            snapshot = self.runtime.process_frame()
            self._render_frame(snapshot.frame)
            self._render_status(snapshot)
        except Exception as exc:
            self.timer.stop()
            self.runtime.close()
            QMessageBox.critical(self, "VisionControl stopped", str(exc))
            self.close()

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
            self.fps_label.setText(f"{self.smoothed_fps:.0f} FPS")
        self.last_frame_time = now

    def _render_status(self, snapshot):
        mode = "PAUSED" if snapshot.paused else "ACTIVE"
        self.status_mode.setText(mode)
        self.status_gesture.setText(humanize(snapshot.gesture))
        self.status_action.setText(snapshot.mouse_status.replace("_", " ").title())
        self.status_keyboard.setText(snapshot.keyboard_state)
        self.status_monitor.setText(snapshot.monitor_name)
        mouse_found = "Detected" if snapshot.mouse_found else "Not detected"
        self.mouse_button.setText(f"Mouse · {mouse_found}")
        self.keyboard_button.setText(f"Keyboard · {snapshot.keyboard_state}")
        progress = (f" · {int(snapshot.arming_progress * 100)}%"
                    if snapshot.arming_progress else "")
        self.gesture_badge.setText(
            f"{humanize(snapshot.gesture).upper()} · {mode}{progress}")
        self.help_label.setText(snapshot.help_text)
        self.tracking_label.setText(
            "● TRACKING" if snapshot.hands else "○ TRACKING · NO HANDS")
        self.tracking_label.setStyleSheet(
            "color: #59d36b; font-weight: 700" if snapshot.hands else
            "color: #f0a54a; font-weight: 700")
        self._update_pause_button()

    def _update_pause_button(self):
        if self.runtime.paused:
            self.pause_button.setText("Resume")
            self.pause_button.setObjectName("primary")
        else:
            self.pause_button.setText("Pause")
            self.pause_button.setObjectName("danger")
        self.pause_button.style().unpolish(self.pause_button)
        self.pause_button.style().polish(self.pause_button)

    def toggle_pause(self):
        self.runtime.toggle_paused()
        self._update_pause_button()

    def open_settings(self):
        self.runtime.set_paused(True)
        self._update_pause_button()
        if self.settings_window is not None:
            self.settings_window.raise_()
            self.settings_window.activateWindow()
            return
        self.settings_window = self.settings_factory(parent=self)
        self.settings_window.settings_saved.connect(self._reload_after_settings)
        self.settings_window.destroyed.connect(self._settings_closed)
        self.settings_window.show()

    def _settings_closed(self):
        self.settings_window = None

    def _reload_after_settings(self):
        self.timer.stop()
        self.runtime.set_paused(True)
        self.runtime.close()
        desktop = load_desktop_settings(APP_SETTINGS)
        profile_path = USER_PROFILE if USER_PROFILE.exists() else None
        try:
            self.runtime = self.runtime_factory(
                desktop.camera_index, True, profile_path)
            self.runtime.start()
            self._refresh_static_runtime_labels()
            self._update_pause_button()
            self.timer.start(16)
        except Exception as exc:
            QMessageBox.critical(self, "Cannot apply settings", str(exc))
            self.close()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.close()
        elif key == Qt.Key.Key_P:
            self.toggle_pause()
        elif key == Qt.Key.Key_C:
            self.runtime.start_calibration()
        elif key == Qt.Key.Key_Space:
            self.runtime.capture_calibration()
        elif key == Qt.Key.Key_R:
            self.runtime.cancel_calibration()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent):
        self.timer.stop()
        self.runtime.close()
        if self.settings_window is not None:
            self.settings_window.close()
        event.accept()


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
    profile_path = args.profile or (USER_PROFILE if USER_PROFILE.exists() else None)

    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("VisionControl")
    app.setStyleSheet(APP_STYLE)
    icon = QIcon(str(ROOT / "docs" / "Vision Control logo.png"))
    app.setWindowIcon(icon)
    runtime = VisionRuntime(camera_index, start_paused, profile_path)
    try:
        import cv2
        startup = StartupScreen(cv2, ROOT / "docs" / "Splash Screen.png",
                                ROOT / "docs" / "Loading Screen.png")
        startup.show_splash(1000)
        runtime.start(lambda value, message:
                      startup.show_loading(value, message,
                                           250 if value >= 1 else 1))
        cv2.destroyAllWindows()
        window = ControllerWindow(runtime)
        window.show()
        if args.quit_after is not None:
            QTimer.singleShot(max(1, int(args.quit_after * 1000)), window.close)
        return app.exec()
    except Exception as exc:
        runtime.close()
        QMessageBox.critical(None, "VisionControl could not start", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
