import json
import subprocess
import sys
from pathlib import Path

from .profile import load_profile
from .settings import (EDITABLE_GESTURES, DesktopSettings,
                       apply_gesture_bindings, load_desktop_settings,
                       save_desktop_settings, save_user_profile)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILE = ROOT / "config" / "default_profile.json"
USER_PROFILE = ROOT / "data" / "user_profile.json"
APP_SETTINGS = ROOT / "data" / "app_settings.json"


def main() -> int:
    try:
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox,
                                       QDoubleSpinBox, QFormLayout, QGridLayout,
                                       QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                                       QMainWindow, QMessageBox, QPushButton,
                                       QSpinBox, QVBoxLayout, QWidget)
    except ImportError as exc:
        raise SystemExit("PySide6 is required. Run: python -m pip install -r requirements.txt") from exc

    class SettingsWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("VisionControl Settings")
            self.setMinimumWidth(620)
            icon = QIcon(str(ROOT / "docs" / "Vision Control logo.png"))
            self.setWindowIcon(icon)
            QApplication.instance().setWindowIcon(icon)

            desktop = load_desktop_settings(APP_SETTINGS)
            profile_path = USER_PROFILE if USER_PROFILE.exists() else DEFAULT_PROFILE
            profile = load_profile(profile_path)
            raw = json.loads(profile_path.read_text(encoding="utf-8"))
            self.raw_profile = raw

            self.camera = QSpinBox(); self.camera.setRange(0, 20); self.camera.setValue(desktop.camera_index)
            self.start_paused = QCheckBox(); self.start_paused.setChecked(desktop.start_paused)
            self.mouse_hand = QComboBox(); self.mouse_hand.addItems(["Right", "Left"]); self.mouse_hand.setCurrentText(profile.mouse_hand)
            self.swap_hands = QCheckBox(); self.swap_hands.setChecked(profile.swap_hands)
            self.monitor_mode = QComboBox(); self.monitor_mode.addItems(["active", "fixed", "all"]); self.monitor_mode.setCurrentText(profile.monitor_mode)
            self.fixed_monitor = QSpinBox(); self.fixed_monitor.setRange(0, 20); self.fixed_monitor.setValue(profile.fixed_monitor)
            self.smoothing = QDoubleSpinBox(); self.smoothing.setRange(.05, 1.0); self.smoothing.setSingleStep(.05); self.smoothing.setValue(float(profile.thresholds.get("cursor_smoothing", .35)))
            self.deadzone = QDoubleSpinBox(); self.deadzone.setRange(0, 30); self.deadzone.setSuffix(" px"); self.deadzone.setValue(float(profile.thresholds.get("cursor_deadzone_px", 2)))
            self.scroll = QDoubleSpinBox(); self.scroll.setRange(1, 200); self.scroll.setValue(float(profile.thresholds.get("scroll_sensitivity", 45)))

            form = QFormLayout()
            form.addRow("Camera index", self.camera)
            form.addRow("Start paused", self.start_paused)
            form.addRow("Mouse hand", self.mouse_hand)
            form.addRow("Swap detected hands", self.swap_hands)
            form.addRow("Monitor mode", self.monitor_mode)
            form.addRow("Fixed monitor index", self.fixed_monitor)
            form.addRow("Cursor smoothing", self.smoothing)
            form.addRow("Cursor deadzone", self.deadzone)
            form.addRow("Scroll sensitivity", self.scroll)

            gesture_labels = {
                "point": "Point (index finger)",
                "peace": "Peace (two fingers)",
                "three_fingers": "Three fingers",
                "four_fingers": "Four fingers",
                "open_palm": "Open palm",
            }
            gesture_group = QGroupBox("Left-hand keyboard gestures")
            gesture_layout = QGridLayout()
            gesture_layout.addWidget(QLabel("Gesture"), 0, 0)
            gesture_layout.addWidget(QLabel("Action"), 0, 1)
            gesture_layout.addWidget(QLabel("Keys (comma separated)"), 0, 2)
            self.gesture_rows = {}
            for row, gesture in enumerate(EDITABLE_GESTURES, start=1):
                binding = profile.bindings.get(gesture)
                action = QComboBox(); action.addItems(["Disabled", "Press", "Hold"])
                keys = QLineEdit(); keys.setPlaceholderText("Example: ctrl, c")
                if binding:
                    action.setCurrentText(binding.action_type.title())
                    keys.setText(", ".join(binding.keys))
                else:
                    action.setCurrentText("Disabled")
                    keys.setEnabled(False)
                action.currentTextChanged.connect(
                    lambda value, editor=keys: editor.setEnabled(value != "Disabled"))
                gesture_layout.addWidget(QLabel(gesture_labels[gesture]), row, 0)
                gesture_layout.addWidget(action, row, 1)
                gesture_layout.addWidget(keys, row, 2)
                self.gesture_rows[gesture] = (action, keys)
            gesture_group.setLayout(gesture_layout)

            note = QLabel("Keyboard hand automatically uses the opposite hand.\nSettings are stored locally and can be changed before each launch.")
            note.setWordWrap(True); note.setStyleSheet("color: #666; margin-top: 8px")
            save_button = QPushButton("Save")
            start_button = QPushButton("Save and Start VisionControl")
            start_button.setDefault(True)
            save_button.clicked.connect(self.save)
            start_button.clicked.connect(self.start)
            buttons = QHBoxLayout(); buttons.addStretch(); buttons.addWidget(save_button); buttons.addWidget(start_button)
            layout = QVBoxLayout(); layout.addLayout(form); layout.addWidget(gesture_group); layout.addWidget(note); layout.addLayout(buttons)
            container = QWidget(); container.setLayout(layout); self.setCentralWidget(container)
            self.monitor_mode.currentTextChanged.connect(self._update_monitor_state)
            self._update_monitor_state()

        def _update_monitor_state(self):
            self.fixed_monitor.setEnabled(self.monitor_mode.currentText() == "fixed")

        def save(self):
            try:
                mouse_hand = self.mouse_hand.currentText()
                raw = json.loads(json.dumps(self.raw_profile))
                raw["mouse_hand"] = mouse_hand
                raw["keyboard_hand"] = "Left" if mouse_hand == "Right" else "Right"
                raw["swap_hands"] = self.swap_hands.isChecked()
                raw["monitor_mode"] = self.monitor_mode.currentText()
                raw["fixed_monitor"] = self.fixed_monitor.value()
                raw.setdefault("thresholds", {})["cursor_smoothing"] = self.smoothing.value()
                raw["thresholds"]["cursor_deadzone_px"] = self.deadzone.value()
                raw["thresholds"]["scroll_sensitivity"] = self.scroll.value()
                selections = {
                    gesture: (action.currentText(), keys.text())
                    for gesture, (action, keys) in self.gesture_rows.items()
                }
                raw = apply_gesture_bindings(raw, selections)
                save_user_profile(USER_PROFILE, raw)
                save_desktop_settings(APP_SETTINGS, DesktopSettings(
                    self.camera.value(), self.start_paused.isChecked()))
                self.raw_profile = raw
                self.statusBar().showMessage("Settings saved", 3000)
                return True
            except Exception as exc:
                QMessageBox.critical(self, "Cannot save settings", str(exc))
                return False

        def start(self):
            if not self.save():
                return
            command = [sys.executable, "-m", "vision_control.app",
                       "--camera-index", str(self.camera.value()),
                       "--profile", str(USER_PROFILE)]
            if self.start_paused.isChecked():
                command.append("--start-paused")
            subprocess.Popen(command, cwd=ROOT)
            self.close()

    app = QApplication(sys.argv)
    app.setApplicationName("VisionControl")
    window = SettingsWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
