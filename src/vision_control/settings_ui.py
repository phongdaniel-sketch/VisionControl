import json
import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QSpinBox,
    QStackedWidget, QVBoxLayout, QWidget,
)

from .paths import resource_root, runtime_data_dir
from .profile import load_profile
from .settings import (
    EDITABLE_GESTURES, DesktopSettings, apply_gesture_bindings,
    load_desktop_settings, save_desktop_settings, save_user_profile,
)
from .ui_theme import APP_STYLE, humanize


ROOT = resource_root()
DEFAULT_PROFILE = ROOT / "config" / "default_profile.json"
USER_PROFILE = runtime_data_dir() / "user_profile.json"
APP_SETTINGS = runtime_data_dir() / "app_settings.json"


class SettingsWindow(QMainWindow):
    settings_saved = Signal()

    def __init__(self, initial_page="General", parent=None):
        super().__init__(parent)
        self.setWindowTitle("VisionControl Settings")
        self.resize(1180, 720)
        self.setMinimumSize(900, 620)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        icon = QIcon(str(ROOT / "docs" / "Vision Control logo.png"))
        self.setWindowIcon(icon)
        if QApplication.instance() is not None:
            QApplication.instance().setWindowIcon(icon)
        self.setStyleSheet(APP_STYLE)

        desktop = load_desktop_settings(APP_SETTINGS)
        profile_path = USER_PROFILE if USER_PROFILE.exists() else DEFAULT_PROFILE
        profile = load_profile(profile_path)
        self.raw_profile = json.loads(profile_path.read_text(encoding="utf-8"))
        self._build_controls(desktop, profile)
        self._build_layout()
        self.open_page(initial_page)
        self._update_monitor_state()

    def _build_controls(self, desktop, profile):
        self.camera = QSpinBox()
        self.camera.setRange(0, 20)
        self.camera.setValue(desktop.camera_index)
        self.start_paused = QCheckBox("Always start paused")
        self.start_paused.setChecked(desktop.start_paused)
        self.mouse_hand = QComboBox()
        self.mouse_hand.addItems(["Right", "Left"])
        self.mouse_hand.setCurrentText(profile.mouse_hand)
        self.swap_hands = QCheckBox("Swap detected hands for mirrored camera")
        self.swap_hands.setChecked(profile.swap_hands)
        self.monitor_mode = QComboBox()
        self.monitor_mode.addItems(["active", "fixed", "all"])
        self.monitor_mode.setCurrentText(profile.monitor_mode)
        self.fixed_monitor = QSpinBox()
        self.fixed_monitor.setRange(0, 20)
        self.fixed_monitor.setValue(profile.fixed_monitor)
        self.smoothing = QDoubleSpinBox()
        self.smoothing.setRange(.05, 1.0)
        self.smoothing.setSingleStep(.05)
        self.smoothing.setValue(float(profile.thresholds.get("cursor_smoothing", .35)))
        self.deadzone = QDoubleSpinBox()
        self.deadzone.setRange(0, 30)
        self.deadzone.setSuffix(" px")
        self.deadzone.setValue(float(profile.thresholds.get("cursor_deadzone_px", 2)))
        self.scroll = QDoubleSpinBox()
        self.scroll.setRange(1, 200)
        self.scroll.setValue(float(profile.thresholds.get("scroll_sensitivity", 45)))
        self.edge_switch = QCheckBox("Enable point-pose edge switching")
        self.edge_switch.setChecked(bool(profile.thresholds.get(
            "monitor_edge_switch_enabled", True)))
        self.edge_dwell = QDoubleSpinBox()
        self.edge_dwell.setRange(.3, 3.0)
        self.edge_dwell.setSingleStep(.1)
        self.edge_dwell.setSuffix(" s")
        self.edge_dwell.setValue(float(profile.thresholds.get(
            "monitor_edge_dwell_seconds", .8)))
        self.edge_zone = QDoubleSpinBox()
        self.edge_zone.setRange(2, 25)
        self.edge_zone.setSuffix(" %")
        self.edge_zone.setValue(float(profile.thresholds.get(
            "monitor_edge_zone", .08)) * 100)

        self.gesture_rows = {}
        for gesture in EDITABLE_GESTURES:
            binding = profile.bindings.get(gesture)
            action = QComboBox()
            action.addItems(["Disabled", "Press", "Hold"])
            keys = QLineEdit()
            keys.setPlaceholderText("Example: ctrl, c")
            if binding:
                action.setCurrentText(binding.action_type.title())
                keys.setText(", ".join(binding.keys))
            else:
                keys.setEnabled(False)
            action.currentTextChanged.connect(
                lambda value, editor=keys: editor.setEnabled(value != "Disabled"))
            self.gesture_rows[gesture] = (action, keys)
        self.monitor_mode.currentTextChanged.connect(self._update_monitor_state)
        self.edge_switch.stateChanged.connect(self._update_monitor_state)

    def _build_layout(self):
        root = QWidget()
        outer = QVBoxLayout(root)
        outer.setContentsMargins(18, 14, 18, 16)
        outer.setSpacing(12)
        header = QHBoxLayout()
        logo = QLabel()
        pixmap = QPixmap(str(ROOT / "docs" / "Vision Control logo.png"))
        logo.setPixmap(pixmap.scaled(38, 38, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation))
        title = QLabel("VisionControl Settings")
        title.setObjectName("sectionTitle")
        header.addWidget(logo)
        header.addWidget(title)
        header.addStretch()
        status = QLabel("Settings are stored locally")
        status.setObjectName("muted")
        header.addWidget(status)
        outer.addLayout(header)

        content = QHBoxLayout()
        content.setSpacing(12)
        sidebar = QFrame()
        sidebar.setObjectName("card")
        sidebar.setFixedWidth(190)
        nav_layout = QVBoxLayout(sidebar)
        nav_layout.setContentsMargins(10, 12, 10, 12)
        nav_layout.setSpacing(4)
        self.nav_buttons = {}
        self.pages = QStackedWidget()
        builders = {
            "General": self._general_page, "Camera": self._camera_page,
            "Mouse": self._mouse_page, "Gestures": self._gestures_page,
            "Keyboard": self._keyboard_page, "Displays": self._displays_page,
            "Advanced": self._advanced_page,
        }
        for name in ("General", "Camera", "Mouse", "Gestures", "Keyboard",
                     "Displays"):
            self._add_nav(name, nav_layout, builders[name]())
        self.voice_button = QPushButton("  Voice · Coming soon")
        self.voice_button.setObjectName("nav")
        self.voice_button.setEnabled(False)
        self.voice_button.setToolTip("Voice control is planned for a future release")
        nav_layout.addWidget(self.voice_button)
        self._add_nav("Advanced", nav_layout, builders["Advanced"]())
        nav_layout.addStretch()
        content.addWidget(sidebar)
        content.addWidget(self.pages, 1)
        outer.addLayout(content, 1)

        footer = QHBoxLayout()
        reset = QPushButton("Reset to defaults")
        reset.clicked.connect(self.reset_defaults)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.close)
        save = QPushButton("Save")
        save.setObjectName("primary")
        save.setDefault(True)
        save.clicked.connect(self.save)
        footer.addWidget(reset)
        footer.addStretch()
        footer.addWidget(cancel)
        footer.addWidget(save)
        outer.addLayout(footer)
        self.setCentralWidget(root)

    def _add_nav(self, name, layout, page):
        button = QPushButton(f"  {name}")
        button.setObjectName("nav")
        button.setCheckable(True)
        button.clicked.connect(lambda _checked=False, page_name=name:
                               self.open_page(page_name))
        layout.addWidget(button)
        self.nav_buttons[name] = button
        self.pages.addWidget(page)

    def _page(self, title, subtitle, body):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        note = QLabel(subtitle)
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(note)
        layout.addSpacing(6)
        layout.addWidget(body)
        layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        return scroll

    @staticmethod
    def _form_group(title):
        group = QGroupBox(title)
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setHorizontalSpacing(24)
        form.setVerticalSpacing(14)
        return group, form

    def _general_page(self):
        group, form = self._form_group("Startup and hand roles")
        form.addRow(self.start_paused)
        form.addRow(self.swap_hands)
        return self._page("General", "Safe startup and mirrored-camera behavior.", group)

    def _camera_page(self):
        group, form = self._form_group("Camera")
        form.addRow("Camera index", self.camera)
        notice = QLabel("The Controller owns the live camera stream. Saving a new camera index restarts tracking in a paused state.")
        notice.setObjectName("muted")
        notice.setWordWrap(True)
        form.addRow(notice)
        return self._page("Camera", "Choose the local camera used for tracking.", group)

    def _mouse_page(self):
        group, form = self._form_group("Mouse control")
        form.addRow("Control hand", self.mouse_hand)
        form.addRow("Cursor smoothing", self.smoothing)
        form.addRow("Cursor deadzone", self.deadzone)
        form.addRow("Scroll sensitivity", self.scroll)
        return self._page("Mouse", "Tune pointer response without changing gesture logic.", group)

    def _gestures_page(self):
        card = QFrame()
        card.setObjectName("card")
        grid = QGridLayout(card)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setSpacing(10)
        descriptions = {
            "point": "Index finger", "peace": "Index + middle",
            "three_fingers": "Three extended fingers",
            "four_fingers": "Four extended fingers", "open_palm": "Open hand",
            "fist": "Reserved for keyboard arm/disarm",
        }
        for index, gesture in enumerate((*EDITABLE_GESTURES, "fist")):
            item = QFrame()
            item.setObjectName("card")
            item_layout = QVBoxLayout(item)
            name = QLabel(humanize(gesture))
            name.setObjectName("sectionTitle")
            detail = QLabel(descriptions[gesture])
            detail.setObjectName("muted")
            detail.setWordWrap(True)
            item_layout.addWidget(name)
            item_layout.addWidget(detail)
            grid.addWidget(item, index // 3, index % 3)
        return self._page("Gestures", "VisionControl's defined gestures; custom training is not implied.", card)

    def _keyboard_page(self):
        group = QGroupBox("Keyboard gesture mapping")
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.addWidget(QLabel("Gesture"), 0, 0)
        grid.addWidget(QLabel("Action"), 0, 1)
        grid.addWidget(QLabel("Key or chord"), 0, 2)
        for row, gesture in enumerate(EDITABLE_GESTURES, start=1):
            action, keys = self.gesture_rows[gesture]
            grid.addWidget(QLabel(humanize(gesture)), row, 0)
            grid.addWidget(action, row, 1)
            grid.addWidget(keys, row, 2)
        note = QLabel("Fist remains reserved for keyboard arming and cannot be mapped.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        grid.addWidget(note, len(EDITABLE_GESTURES) + 1, 0, 1, 3)
        return self._page("Keyboard", "Configure Disabled, Press, Hold, and multi-key chords.", group)

    def _displays_page(self):
        group, form = self._form_group("Display mapping")
        form.addRow("Monitor mode", self.monitor_mode)
        form.addRow("Fixed monitor index", self.fixed_monitor)
        form.addRow(self.edge_switch)
        form.addRow("Edge dwell time", self.edge_dwell)
        form.addRow("Edge zone", self.edge_zone)
        return self._page("Displays", "Configure active, fixed, or all-display pointer mapping.", group)

    def _advanced_page(self):
        group = QGroupBox("Safety and local data")
        layout = QVBoxLayout(group)
        text = QLabel("Camera frames remain local. Pause, hand loss, calibration, Settings, exit, and exceptions release held input. Profiles and calibration are stored in the operating system's application-data directory.")
        text.setWordWrap(True)
        text.setObjectName("muted")
        layout.addWidget(text)
        return self._page("Advanced", "Runtime safety and storage behavior.", group)

    def open_page(self, name):
        selected = name if name in self.nav_buttons else "General"
        button = self.nav_buttons[selected]
        for candidate in self.nav_buttons.values():
            candidate.setChecked(candidate is button)
        self.pages.setCurrentIndex(list(self.nav_buttons).index(selected))

    def _update_monitor_state(self):
        mode = self.monitor_mode.currentText()
        self.fixed_monitor.setEnabled(mode == "fixed")
        self.edge_switch.setEnabled(mode == "active")
        enabled = mode == "active" and self.edge_switch.isChecked()
        self.edge_dwell.setEnabled(enabled)
        self.edge_zone.setEnabled(enabled)

    def reset_defaults(self):
        self.raw_profile = json.loads(DEFAULT_PROFILE.read_text(encoding="utf-8"))
        profile = load_profile(DEFAULT_PROFILE)
        self.camera.setValue(0)
        self.start_paused.setChecked(True)
        self.mouse_hand.setCurrentText(profile.mouse_hand)
        self.swap_hands.setChecked(profile.swap_hands)
        self.monitor_mode.setCurrentText(profile.monitor_mode)
        self.fixed_monitor.setValue(profile.fixed_monitor)
        self.smoothing.setValue(profile.thresholds["cursor_smoothing"])
        self.deadzone.setValue(profile.thresholds["cursor_deadzone_px"])
        self.scroll.setValue(profile.thresholds["scroll_sensitivity"])
        self.edge_switch.setChecked(profile.thresholds["monitor_edge_switch_enabled"])
        self.edge_dwell.setValue(profile.thresholds["monitor_edge_dwell_seconds"])
        self.edge_zone.setValue(profile.thresholds["monitor_edge_zone"] * 100)
        for gesture, (action, keys) in self.gesture_rows.items():
            binding = profile.bindings.get(gesture)
            action.setCurrentText(binding.action_type.title() if binding else "Disabled")
            keys.setText(", ".join(binding.keys) if binding else "")
        self.statusBar().showMessage("Defaults loaded; press Save to apply", 4000)

    def save(self):
        try:
            mouse_hand = self.mouse_hand.currentText()
            raw = json.loads(json.dumps(self.raw_profile))
            raw["mouse_hand"] = mouse_hand
            raw["keyboard_hand"] = "Left" if mouse_hand == "Right" else "Right"
            raw["swap_hands"] = self.swap_hands.isChecked()
            raw["monitor_mode"] = self.monitor_mode.currentText()
            raw["fixed_monitor"] = self.fixed_monitor.value()
            thresholds = raw.setdefault("thresholds", {})
            thresholds["cursor_smoothing"] = self.smoothing.value()
            thresholds["cursor_deadzone_px"] = self.deadzone.value()
            thresholds["scroll_sensitivity"] = self.scroll.value()
            thresholds["monitor_edge_switch_enabled"] = self.edge_switch.isChecked()
            thresholds["monitor_edge_dwell_seconds"] = self.edge_dwell.value()
            thresholds["monitor_edge_zone"] = self.edge_zone.value() / 100
            selections = {gesture: (action.currentText(), keys.text())
                          for gesture, (action, keys) in self.gesture_rows.items()}
            raw = apply_gesture_bindings(raw, selections)
            save_user_profile(USER_PROFILE, raw)
            save_desktop_settings(APP_SETTINGS, DesktopSettings(
                self.camera.value(), self.start_paused.isChecked()))
            self.raw_profile = raw
            self.settings_saved.emit()
            self.close()
            return True
        except Exception as exc:
            QMessageBox.critical(self, "Cannot save settings", str(exc))
            return False


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("VisionControl")
    app.setStyleSheet(APP_STYLE)
    window = SettingsWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
