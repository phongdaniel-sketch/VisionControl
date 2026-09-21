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
from .monitors import discover_monitors
from .profile import load_profile
from .settings import (
    EDITABLE_GESTURES, DesktopSettings, apply_gesture_bindings,
    load_desktop_settings, save_desktop_settings, save_user_profile,
)
from .ui_theme import APP_STYLE, humanize
from .settings_widgets import StateCheckBox as QCheckBox


ROOT = resource_root()
DEFAULT_PROFILE = ROOT / "config" / "gesture_v1_profile.json"
USER_PROFILE = runtime_data_dir() / "user_profile.json"
APP_SETTINGS = runtime_data_dir() / "app_settings.json"


class SettingsWindow(QMainWindow):
    settings_saved = Signal()
    debug_recording_requested = Signal()

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
        for control in self.findChildren(QSpinBox) + self.findChildren(QDoubleSpinBox):
            control.setMinimumWidth(120)
            control.setMaximumWidth(180)
        self.open_page(initial_page)
        self._update_monitor_state()

    def _build_controls(self, desktop, profile):
        from .camera_devices import CameraPicker
        self.camera = CameraPicker(desktop.camera_index)
        self.show_skeleton = QCheckBox('Hand skeleton and colored points')
        self.show_skeleton.setChecked(desktop.show_skeleton)
        self.show_guide = QCheckBox('Gesture guide beside the camera')
        self.show_guide.setChecked(desktop.show_guide)
        self.debug_view = QCheckBox('Debug details (this session)')
        self.debug_view.setChecked(bool(getattr(getattr(self.parent(), 'runtime', None), 'debug_enabled', False)))
        self.open_recording_after_save = False
        self._describe(self.camera,
                       "Camera device index. Try 0 first on Windows; choose the index "
                       "of your physical camera if a virtual camera is also installed.")
        self.start_paused = QCheckBox("Always start paused")
        self.start_paused.setChecked(desktop.start_paused)
        self._describe(self.start_paused,
                       "Applies on the next normal launch after Save. --start-paused overrides Off. "
                       "Closing Settings or calibration always leaves control paused.")
        self.mouse_hand = QComboBox()
        self.mouse_hand.addItems(["Right", "Left"])
        self.mouse_hand.setCurrentText(profile.mouse_hand)
        self._describe(self.mouse_hand,
                       "Hand used for pointer movement, pinch clicks, drag, and scrolling.")
        self.pointer_mode = QComboBox()
        self.pointer_mode.addItem("Palm (default)", "palm")
        self.pointer_mode.addItem("Index fingertip", "thumb_lock")
        self._set_combo_data(self.pointer_mode, 'thumb_lock' if profile.pointer_mode in {'thumb_lock', 'index_fingertip'} else 'palm')
        self._describe(self.pointer_mode,
                       "Palm follows palm center without thumb locking. Index fingertip locks when the thumb opens. "
                       "Both use the same gestures; calibration is saved separately.")
        self.swap_hands = QCheckBox("Swap left / right hands")
        self.swap_hands.setChecked(profile.swap_hands)
        self._describe(self.swap_hands,
                       "Corrects Left/Right labels when the camera preview is mirrored.")
        self.monitor_mode = QComboBox()
        self.monitor_mode.addItems(["active", "fixed", "all"])
        self.monitor_mode.setCurrentText(profile.monitor_mode)
        self._describe(
            self.monitor_mode,
            "fixed confines the pointer to one display; active follows the display "
            "containing the cursor; all maps across the combined desktop.")
        self.fixed_monitor = QComboBox()
        self.fixed_monitor.setMinimumWidth(330)
        self._populate_fixed_displays(profile.fixed_monitor)
        self._describe(self.fixed_monitor,
                       "Display used by fixed mode. The Primary display is listed first.")
        self.smoothing = QDoubleSpinBox()
        self.smoothing.setRange(.05, 1.0)
        self.smoothing.setSingleStep(.05)
        self.smoothing.setDecimals(2)
        self._describe(
            self.smoothing,
            "Higher values follow your hand faster; lower values filter more jitter.")
        self.smoothing.setValue(float(profile.thresholds.get("cursor_smoothing", .6)))
        self.adaptive_smoothing = QCheckBox("Adapt smoothing to movement")
        self.adaptive_smoothing.setChecked(bool(profile.thresholds.get(
            "cursor_adaptive_smoothing", False)))
        self._describe(self.adaptive_smoothing,
                       "Filters small movements more strongly and follows large movements faster. "
                       "Response is adjusted for processing frame rate.")
        self.pinch_confirm = QDoubleSpinBox()
        self.pinch_confirm.setRange(0, .5)
        self.pinch_confirm.setDecimals(2)
        self.pinch_confirm.setSingleStep(.02)
        self.pinch_confirm.setSuffix(" s")
        self.pinch_confirm.setValue(float(profile.thresholds.get("pinch_confirm_seconds", .08)))
        self.pinch_release = QDoubleSpinBox()
        self.pinch_release.setRange(.04, .5)
        self.pinch_release.setDecimals(2)
        self.pinch_release.setSingleStep(.01)
        self.pinch_release.setSuffix(' s')
        self.pinch_release.setValue(float(profile.thresholds.get('pinch_release_seconds', .1)))
        self._describe(self.pinch_release,'Thumb-lock drag: continuously separated time before release. Pause/hand loss releases immediately.')
        self._describe(self.pinch_confirm,
                       "Keep one clear pinch closed this long before a click starts. "
                       "Higher values reject brief false clicks. Release remains immediate.")
        self.deadzone = QDoubleSpinBox()
        self.deadzone.setRange(0, 30)
        self.deadzone.setSingleStep(.5)
        self.deadzone.setDecimals(1)
        self.deadzone.setSuffix(" px")
        self._describe(
            self.deadzone,
            "Minimum pointer movement sent to the OS. Lower values detect finer motion; "
            "increase only if the pointer jitters.")
        self.deadzone.setValue(float(profile.thresholds.get("cursor_deadzone_px", .5)))
        self.scroll = QDoubleSpinBox()
        self.scroll.setRange(1, 200)
        self.scroll.setValue(float(profile.thresholds.get("scroll_sensitivity", 45)))
        self._describe(self.scroll,
                       "Distance scrolled for a two-finger vertical movement. Higher is faster.")
        self.edge_switch = QCheckBox("Point-pose display switching (legacy)")
        self.edge_switch.setChecked(bool(profile.thresholds.get(
            "monitor_edge_switch_enabled", True)))
        self._describe(self.edge_switch,
                       "Legacy pointer only: extend index, curl the other fingers and hold near "
                       "a left/right edge to change displays in active monitor mode. "
                       "Not implemented for Palm or the current Index fingertip mode.")
        self.edge_dwell = QDoubleSpinBox()
        self.edge_dwell.setRange(.3, 3.0)
        self.edge_dwell.setSingleStep(.1)
        self.edge_dwell.setSuffix(" s")
        self.edge_dwell.setValue(float(profile.thresholds.get(
            "monitor_edge_dwell_seconds", .8)))
        self._describe(self.edge_dwell,
                       "How long Point must remain at a display edge before switching.")
        self.edge_zone = QDoubleSpinBox()
        self.edge_zone.setRange(2, 25)
        self.edge_zone.setSuffix(" %")
        self.edge_zone.setValue(float(profile.thresholds.get(
            "monitor_edge_zone", .08)) * 100)
        self._describe(self.edge_zone,
                       "Width of the left/right switching area as a percentage of the camera range.")

        self.arm_hold = QDoubleSpinBox()
        self.arm_hold.setRange(.3, 3.0)
        self.arm_hold.setSingleStep(.1)
        self.arm_hold.setSuffix(" s")
        self.arm_hold.setValue(profile.arming.hold_seconds)
        self._describe(self.arm_hold,
                       "How long to hold Fist before keyboard gestures arm or disarm.")
        self.arm_release_frames = QSpinBox()
        self.arm_release_frames.setRange(1, 15)
        self.arm_release_frames.setValue(profile.arming.release_frames)
        self._describe(self.arm_release_frames,
                       "Non-fist frames required before another Fist toggle is accepted.")
        self.arm_cooldown = QDoubleSpinBox()
        self.arm_cooldown.setRange(0, 3.0)
        self.arm_cooldown.setSingleStep(.1)
        self.arm_cooldown.setSuffix(" s")
        self.arm_cooldown.setValue(profile.arming.cooldown_seconds)
        self._describe(self.arm_cooldown,
                       "Minimum delay after an arm/disarm toggle before another can begin.")
        self.auto_disarm = QDoubleSpinBox()
        self.auto_disarm.setRange(.2, 10.0)
        self.auto_disarm.setSingleStep(.1)
        self.auto_disarm.setSuffix(" s")
        self.auto_disarm.setValue(profile.arming.auto_disarm_seconds)
        self._describe(self.auto_disarm,
                       "Automatically disarm keyboard gestures after the keyboard hand is lost.")

        thresholds = profile.thresholds
        self.gesture_confidence = QDoubleSpinBox()
        self.gesture_confidence.setRange(.5, .95)
        self.gesture_confidence.setSingleStep(.05)
        self.gesture_confidence.setDecimals(2)
        self.gesture_confidence.setValue(float(thresholds.get("gesture_confidence", .7)))
        self._describe(self.gesture_confidence,
                       "Minimum MediaPipe hand confidence. Higher rejects uncertain detections "
                       "but may ignore a partially visible hand.")
        self.gesture_on_frames = QSpinBox()
        self.gesture_on_frames.setRange(1, 10)
        self.gesture_on_frames.setValue(int(thresholds.get("gesture_on_frames", 3)))
        self._describe(self.gesture_on_frames,
                       "Consecutive matching frames before a keyboard action fires. "
                       "Lower is faster; higher reduces accidental triggers.")
        self.pinch_close = QDoubleSpinBox()
        self.pinch_close.setRange(.1, .75)
        self.pinch_close.setSingleStep(.05)
        self.pinch_close.setDecimals(2)
        self.pinch_close.setValue(float(thresholds.get("pinch_close_ratio", .35)))
        self._describe(self.pinch_close,
                       "Thumb-to-finger distance that starts a pinch. Must be lower than Pinch release.")
        self.pinch_open = QDoubleSpinBox()
        self.pinch_open.setRange(.15, .9)
        self.pinch_open.setSingleStep(.05)
        self.pinch_open.setDecimals(2)
        self.pinch_open.setValue(float(thresholds.get("pinch_open_ratio", .5)))
        self._describe(self.pinch_open,
                       "Thumb-to-finger distance that releases a pinch. Must exceed Pinch start.")
        self.drag_hold = QDoubleSpinBox()
        self.drag_hold.setRange(.1, 2.0)
        self.drag_hold.setSingleStep(.1)
        self.drag_hold.setSuffix(" s")
        self.drag_hold.setValue(float(thresholds.get("drag_hold_seconds", .4)))
        self._describe(self.drag_hold,
                       "Time a pinch stays closed before its status changes from click to drag.")
        self.scroll_deadzone = QDoubleSpinBox()
        self.scroll_deadzone.setRange(.001, .1)
        self.scroll_deadzone.setSingleStep(.005)
        self.scroll_deadzone.setDecimals(3)
        self.scroll_deadzone.setValue(float(thresholds.get("scroll_deadzone", .015)))
        self._describe(self.scroll_deadzone,
                       "Minimum two-finger vertical motion before scrolling. Lower is more sensitive.")

        self.mouse_move_gesture = QComboBox()
        for label, value in (
                ("Any visible pose", "any"), ("Point", "point"),
                ("Peace", "peace"), ("Three fingers", "three_fingers"),
                ("Four fingers", "four_fingers"), ("Open palm", "open_palm")):
            self.mouse_move_gesture.addItem(label, value)
        self._set_combo_data(
            self.mouse_move_gesture,
            str(thresholds.get("mouse_move_gesture", "any")))
        self._describe(
            self.mouse_move_gesture,
            "Pose allowed to move the pointer. Any visible pose preserves the current behavior.")
        self.mouse_primary_click = self._click_gesture_combo(
            str(thresholds.get("mouse_primary_click_gesture", "pinch_index")))
        self._describe(self.mouse_primary_click,
                       "Gesture that holds the primary/left mouse button for click and drag.")
        self.mouse_secondary_click = self._click_gesture_combo(
            str(thresholds.get("mouse_secondary_click_gesture", "pinch_middle")))
        self._describe(self.mouse_secondary_click,
                       "Gesture that holds the secondary/right mouse button for click and drag.")
        self.mouse_scroll_gesture = QComboBox()
        for label, value in (
                ("Peace", "peace"), ("Three fingers", "three_fingers"),
                ("Four fingers", "four_fingers"), ("Open palm", "open_palm")):
            self.mouse_scroll_gesture.addItem(label, value)
        self._set_combo_data(
            self.mouse_scroll_gesture,
            str(thresholds.get("mouse_scroll_gesture", "peace")))
        self._describe(self.mouse_scroll_gesture,
                       "Pose used for vertical hand-motion scrolling.")

        self.gesture_rows = {}
        for gesture in EDITABLE_GESTURES:
            binding = profile.bindings.get(gesture)
            action = QComboBox()
            action.addItems(["Disabled", "Press", "Hold"])
            self._describe(action,
                           "Disabled does nothing; Press sends once after recognition; "
                           "Hold keeps the configured keys down while the pose remains stable.")
            keys = QLineEdit()
            keys.setPlaceholderText("Example: ctrl, c")
            self._describe(keys,
                           "Key or comma-separated chord, for example: space, w, or ctrl, c.")
            if binding:
                action.setCurrentText(binding.action_type.title())
                keys.setText(", ".join(binding.keys))
            else:
                keys.setEnabled(False)
            action.currentTextChanged.connect(
                lambda value, editor=keys: editor.setEnabled(value != "Disabled"))
            self.gesture_rows[gesture] = (action, keys)
        self.monitor_mode.currentTextChanged.connect(self._update_monitor_state)
        self.pointer_mode.currentIndexChanged.connect(self._update_monitor_state)
        self.edge_switch.stateChanged.connect(self._update_monitor_state)
        self.mouse_hand.currentTextChanged.connect(self._refresh_gesture_hand_labels)

    @staticmethod
    def _describe(widget, text):
        widget.setToolTip(text)
        widget.setAccessibleDescription(text)

    def _click_gesture_combo(self, selected):
        combo = QComboBox()
        for label, value in (
                ("Disabled", "disabled"),
                ("Index pinch", "pinch_index"),
                ("Middle pinch", "pinch_middle")):
            combo.addItem(label, value)
        self._set_combo_data(combo, selected)
        return combo

    @staticmethod
    def _set_combo_data(combo, value):
        selected = combo.findData(value)
        combo.setCurrentIndex(selected if selected >= 0 else 0)

    def _refresh_gesture_hand_labels(self):
        if not hasattr(self, "gesture_hand_selector"):
            return
        selected = self.gesture_hand_selector.currentIndex()
        mouse_hand = self.mouse_hand.currentText()
        keyboard_hand = "Left" if mouse_hand == "Right" else "Right"
        self.gesture_hand_selector.setItemText(0, f"Mouse hand · {mouse_hand}")
        self.gesture_hand_selector.setItemText(1, f"Keyboard hand · {keyboard_hand}")
        self.gesture_hand_selector.setCurrentIndex(selected)

    def _populate_fixed_displays(self, selected_index):
        layout = discover_monitors("fixed", 0)
        qt_screens = list(QApplication.screens())
        primary_screen = QApplication.primaryScreen()
        ordered_qt_screens = sorted(
            qt_screens, key=lambda candidate: candidate is not primary_screen)
        for index, region in enumerate(layout.regions):
            screen = next((candidate for candidate in qt_screens
                           if self._screen_geometry(candidate) ==
                           (region.x, region.y, region.width, region.height)), None)
            if screen is None and index < len(ordered_qt_screens):
                # macOS uses different vertical coordinate origins in Qt and
                # screeninfo; their primary-first enumeration remains aligned.
                screen = ordered_qt_screens[index]
            name = screen.name().strip() if screen is not None else ""
            if not name or name.lower() in {"unknown", "unnamed"}:
                name = (region.name if not region.name.startswith("display-")
                        else f"Display {index + 1}")
            is_primary = region.is_primary or screen is primary_screen
            primary = " · Primary" if is_primary else ""
            self.fixed_monitor.addItem(
                f"{name} · {region.width} × {region.height}{primary}", index)
        self._set_fixed_monitor(selected_index)

    @staticmethod
    def _screen_geometry(screen):
        geometry = screen.geometry()
        return (geometry.x(), geometry.y(), geometry.width(), geometry.height())

    def _set_fixed_monitor(self, index):
        selected = self.fixed_monitor.findData(int(index))
        self.fixed_monitor.setCurrentIndex(selected if selected >= 0 else 0)

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
            "Mouse": self._mouse_page, "Gestures": self._current_gestures_page,
            "Preview & Debug": self._preview_page, "Displays": self._displays_page,
        }
        for name in ("General", "Camera", "Mouse", "Gestures", "Preview & Debug",
                     "Displays"):
            self._add_nav(name, nav_layout, builders[name]())
        self.voice_button = QPushButton("  Voice · Coming soon")
        self.voice_button.setObjectName("nav")
        self.voice_button.setEnabled(False)
        self._describe(self.voice_button,
                       "Voice control is planned for a future release.")
        nav_layout.addWidget(self.voice_button)
        self.voice_button.hide()
        nav_layout.addStretch()
        content.addWidget(sidebar)
        content.addWidget(self.pages, 1)
        outer.addLayout(content, 1)

        footer = QHBoxLayout()
        reset = QPushButton("Reset to defaults")
        reset.clicked.connect(self.reset_defaults)
        self._describe(reset,
                       "Load the recommended defaults into this window. Press Save to apply them.")
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.close)
        self._describe(cancel, "Close Settings without saving changes.")
        save = QPushButton("Save")
        save.setObjectName("primary")
        save.setDefault(True)
        save.clicked.connect(self.save)
        self._describe(save,
                       "Validate and save locally, then restart tracking in a paused state.")
        footer.addWidget(reset)
        footer.addStretch()
        footer.addWidget(cancel)
        footer.addWidget(save)
        outer.addLayout(footer)
        self.setCentralWidget(root)

    def _add_nav(self, name, layout, page):
        button = QPushButton("  " + name.replace("&", "&&"))
        button.setObjectName("nav")
        button.setCheckable(True)
        self._describe(button, f"Open the {name} settings page.")
        button.clicked.connect(lambda _checked=False, page_name=name:
                               self.open_page(page_name))
        layout.addWidget(button)
        self.nav_buttons[name] = button
        self.pages.addWidget(page)

    def _current_gestures_page(self):
        from .gesture_v1_ui import GestureV1Panel
        self.v1_panel = GestureV1Panel(self.raw_profile.get('gesture_v1'), (
            ('Pinch start distance (ratio)', self.pinch_close),
            ('Pinch release distance (ratio)', self.pinch_open),
            ('Drag start confirmation', self.pinch_confirm),
            ('Drag release confirmation', self.pinch_release),
        ))
        return self._page('Gestures', 'Hand actions and shortcuts for both pointer modes', self.v1_panel)

    def _v1_mapping_state(self, enabled):
        for action, keys in self.gesture_rows.values():
            action.setEnabled(not enabled)
            keys.setEnabled(not enabled)
            action.setToolTip('Use Gesture v1 for the new 1–5 finger bindings.' if enabled else
                              'Choose Disabled, Press or Hold for this legacy gesture.')

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
        startup_hint = QLabel('On: wait for Start. Off: a normal launch may enable control immediately. '
            'Save applies this to the next launch; closing Settings never starts control. '
            'An explicit --start-paused or windows.ps1 run -StartPaused overrides Off. '
            'Normal windows.ps1 run follows this saved setting.')
        startup_hint.setWordWrap(True)
        startup_hint.setObjectName('muted')
        form.addRow(startup_hint)
        form.addRow(self.swap_hands)
        hint = QLabel('Enable hand swapping only if the app labels your left and right hands incorrectly.')
        hint.setWordWrap(True)
        hint.setObjectName('muted')
        form.addRow(hint)
        return self._page("General", "Choose how the app starts and identifies your hands.", group)

    def _camera_page(self):
        group, form = self._form_group("Camera")
        form.addRow("Camera", self.camera)
        refresh = QPushButton('Refresh camera list')
        refresh.clicked.connect(lambda: self.camera.refresh())
        form.addRow(refresh)
        notice = QLabel("Choose your webcam by name. If unplugged, its saved number stays listed. Saving restarts the camera with control paused.")
        notice.setObjectName("muted")
        notice.setWordWrap(True)
        form.addRow(notice)
        return self._page("Camera", "Choose the local camera used for tracking.", group)

    def _preview_page(self):
        group, form = self._form_group('Preview and diagnostics')
        form.addRow(self.show_skeleton)
        form.addRow(self.show_guide)
        form.addRow(self.debug_view)
        self.recording_button = QPushButton('Save && open Debug recording')
        self.recording_button.setEnabled(self.debug_view.isChecked() and self.parent() is not None)
        self.debug_view.toggled.connect(lambda enabled: self.recording_button.setEnabled(enabled and self.parent() is not None))
        self.recording_button.clicked.connect(self._request_recording)
        form.addRow(self.recording_button)
        note = QLabel('Debug starts Off each time you launch the app. Recording opens a test window; press Start there to record. Open these Settings from the Controller to use recording.')
        note.setWordWrap(True)
        form.addRow(note)
        return self._page('Preview & Debug', 'Choose what to show and open the local recorder.', group)

    def _request_recording(self):
        self.open_recording_after_save = True
        if self.save():
            self.debug_recording_requested.emit()
        else:
            self.open_recording_after_save = False

    def _mouse_page(self):
        group, form = self._form_group("Mouse control")
        form.addRow("Control hand", self.mouse_hand)
        form.addRow("Pointer mode", self.pointer_mode)
        form.addRow("Cursor response", self.smoothing)
        form.addRow(self.adaptive_smoothing)
        form.addRow("Movement deadzone", self.deadzone)
        note = QLabel(
            "Palm: opening the thumb enables clicks without locking the pointer. "
            "Index fingertip: opening the thumb locks the pointer for clicks. "
            "Pinch drags in both modes. Calibrate each mode separately. "
            "Configure scroll and other actions in Gestures.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        form.addRow(note)
        return self._page("Mouse", "Choose pointer mode and tune its response.", group)

    def _gestures_page(self):
        body = QFrame()
        body.setObjectName("card")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        self.gesture_hand_selector = QComboBox()
        self.gesture_hand_selector.addItems(["Mouse hand", "Keyboard hand"])
        self._describe(
            self.gesture_hand_selector,
            "Choose which hand role you are configuring. Hand sides follow Mouse settings.")
        self._refresh_gesture_hand_labels()
        self.gesture_hand_pages = QStackedWidget()
        self.gesture_hand_pages.addWidget(self._mouse_gesture_mapping_widget())
        self.gesture_hand_pages.addWidget(self._keyboard_gesture_mapping_widget())
        self.gesture_hand_selector.currentIndexChanged.connect(
            self.gesture_hand_pages.setCurrentIndex)
        layout.addWidget(self.gesture_hand_selector)
        layout.addWidget(self.gesture_hand_pages)
        return self._page(
            "Gestures",
            "Configure mouse-hand controls and keyboard-hand shortcuts separately.",
            body,
        )

    def _mouse_gesture_mapping_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        group, form = self._form_group("Mouse-hand mapping")
        form.addRow("Move pointer", self.mouse_move_gesture)
        mode_note = QLabel("Thumb lock: open thumb to freeze. Curl/re-extend index = left, "
                           "both = middle. Thumb + middle contact = right click. Index pinch = drag. "
                           "The mappings below apply to the other pointer modes.")
        mode_note.setWordWrap(True)
        mode_note.setObjectName("muted")
        form.addRow(mode_note)
        self.pointer_mode.currentIndexChanged.connect(
            lambda: self.mouse_move_gesture.setEnabled(
                self.pointer_mode.currentData() == "gesture"))
        self.mouse_move_gesture.setEnabled(self.pointer_mode.currentData() == "gesture")
        def update_click_editors():
            enabled = self.pointer_mode.currentData() != 'thumb_lock'
            for editor in (self.mouse_primary_click, self.mouse_secondary_click, self.mouse_scroll_gesture):
                editor.setEnabled(enabled)
        self.pointer_mode.currentIndexChanged.connect(update_click_editors)
        update_click_editors()
        form.addRow("Primary click / drag", self.mouse_primary_click)
        form.addRow("Secondary click / drag", self.mouse_secondary_click)
        form.addRow("Scroll", self.mouse_scroll_gesture)
        fist = QLabel("Fist · Stop pointer and release mouse buttons · Safety locked")
        fist.setStyleSheet("color: #ffb36b; font-weight: 600")
        fist.setToolTip(
            "Fist always stops the pointer and releases held mouse buttons.")
        note = QLabel(
            "Primary and secondary clicks must use different pinches. A selected "
            "movement pose must also differ from the scroll pose. Extend the clicking "
            "finger with the thumb apart, then pinch within 0.8 seconds. Open both pinches before "
            "switching buttons. Adjust Pinch confirmation in Advanced.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        form.addRow(fist)
        form.addRow(note)
        layout.addWidget(group)
        return widget

    def _keyboard_gesture_mapping_widget(self):
        card = QFrame()
        card.setObjectName("card")
        grid = QGridLayout(card)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setSpacing(10)
        descriptions = {
            "point": "Index finger", "peace": "Index + middle",
            "three_fingers": "Three extended fingers",
            "four_fingers": "Four extended fingers", "open_palm": "Open hand",
            "fist": "No keyboard toggle; modifier support pending",
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
            if gesture in self.gesture_rows:
                action, keys = self.gesture_rows[gesture]
                item_layout.addWidget(action)
                item_layout.addWidget(keys)
            else:
                locked = QLabel("No action assigned")
                locked.setStyleSheet("color: #ffb36b; font-weight: 600")
                locked.setToolTip(
                    "Legacy fist arming has been removed. New modifier gestures are pending.")
                item_layout.addWidget(locked)
            grid.addWidget(item, index // 3, index % 3)
        note = QLabel(
            "Configure what each built-in pose does. This changes actions and shortcuts; "
            "it does not train a new hand pose.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        grid.addWidget(note, 2, 0, 1, 3)
        return card

    def _keyboard_page(self):
        group, form = self._form_group("Keyboard control")
        note = QLabel(
            "Fist arming has been removed. Keyboard bindings work while ACTIVE. Pause, "
            "Settings, hand loss, calibration, errors, and exit release held keys.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        form.addRow(note)
        return self._page(
            "Keyboard", "Edit key bindings in Gestures. Use Pause to stop input.", group)

    def _displays_page(self):
        group, form = self._form_group("Display mapping")
        form.addRow("Monitor mode", self.monitor_mode)
        form.addRow("Fixed display", self.fixed_monitor)
        form.addRow(self.edge_switch)
        self.edge_switch_note = QLabel()
        self.edge_switch_note.setWordWrap(True)
        self.edge_switch_note.setObjectName('muted')
        form.addRow(self.edge_switch_note)
        form.addRow("Edge dwell time", self.edge_dwell)
        form.addRow("Edge zone", self.edge_zone)
        return self._page(
            "Displays",
            "Fixed confines the pointer to one display; display 0 is always the primary display.",
            group,
        )

    def open_page(self, name):
        selected = name if name in self.nav_buttons else "General"
        button = self.nav_buttons[selected]
        for candidate in self.nav_buttons.values():
            candidate.setChecked(candidate is button)
        self.pages.setCurrentIndex(list(self.nav_buttons).index(selected))

    def _update_monitor_state(self):
        mode = self.monitor_mode.currentText()
        self.fixed_monitor.setEnabled(mode == "fixed")
        supported = self.pointer_mode.currentData() not in {'palm', 'thumb_lock'}
        self.edge_switch.setEnabled(mode == "active" and supported)
        enabled = mode == "active" and supported and self.edge_switch.isChecked()
        self.edge_dwell.setEnabled(enabled)
        self.edge_zone.setEnabled(enabled)
        if hasattr(self, 'edge_switch_note'):
            self.edge_switch_note.setText(
                'Unavailable in Palm and current Index fingertip modes. The stored On/Off value '
                'has no effect here. Use Fixed to select one display, or All for the combined desktop.'
                if not supported else 'Requires Active monitor mode and at least two displays.')

    def reset_defaults(self):
        self.raw_profile = json.loads(DEFAULT_PROFILE.read_text(encoding="utf-8"))
        self.v1_panel.load(self.raw_profile.get('gesture_v1'))
        profile = load_profile(DEFAULT_PROFILE)
        self.camera.setValue(DesktopSettings().camera_index)
        self.show_skeleton.setChecked(True)
        self.show_guide.setChecked(True)
        self.debug_view.setChecked(False)
        self.start_paused.setChecked(True)
        self.mouse_hand.setCurrentText(profile.mouse_hand)
        self._set_combo_data(self.pointer_mode, 'thumb_lock' if profile.pointer_mode in {'thumb_lock', 'index_fingertip'} else 'palm')
        self.swap_hands.setChecked(profile.swap_hands)
        self.monitor_mode.setCurrentText(profile.monitor_mode)
        self._set_fixed_monitor(profile.fixed_monitor)
        self.smoothing.setValue(profile.thresholds["cursor_smoothing"])
        self.adaptive_smoothing.setChecked(profile.thresholds.get("cursor_adaptive_smoothing", False))
        self.pinch_confirm.setValue(profile.thresholds.get("pinch_confirm_seconds", .08))
        self.pinch_release.setValue(profile.thresholds.get('pinch_release_seconds', .1))
        self.deadzone.setValue(profile.thresholds["cursor_deadzone_px"])
        self.scroll.setValue(profile.thresholds["scroll_sensitivity"])
        self.edge_switch.setChecked(profile.thresholds["monitor_edge_switch_enabled"])
        self.edge_dwell.setValue(profile.thresholds["monitor_edge_dwell_seconds"])
        self.edge_zone.setValue(profile.thresholds["monitor_edge_zone"] * 100)
        self.arm_hold.setValue(profile.arming.hold_seconds)
        self.arm_release_frames.setValue(profile.arming.release_frames)
        self.arm_cooldown.setValue(profile.arming.cooldown_seconds)
        self.auto_disarm.setValue(profile.arming.auto_disarm_seconds)
        self.gesture_confidence.setValue(profile.thresholds["gesture_confidence"])
        self.gesture_on_frames.setValue(profile.thresholds["gesture_on_frames"])
        self.pinch_close.setValue(profile.thresholds["pinch_close_ratio"])
        self.pinch_open.setValue(profile.thresholds["pinch_open_ratio"])
        self.drag_hold.setValue(profile.thresholds["drag_hold_seconds"])
        self.scroll_deadzone.setValue(profile.thresholds["scroll_deadzone"])
        self._set_combo_data(
            self.mouse_move_gesture,
            profile.thresholds.get("mouse_move_gesture", "any"))
        self._set_combo_data(
            self.mouse_primary_click,
            profile.thresholds.get("mouse_primary_click_gesture", "pinch_index"))
        self._set_combo_data(
            self.mouse_secondary_click,
            profile.thresholds.get("mouse_secondary_click_gesture", "pinch_middle"))
        self._set_combo_data(
            self.mouse_scroll_gesture,
            profile.thresholds.get("mouse_scroll_gesture", "peace"))
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
            raw["pointer_mode"] = self.pointer_mode.currentData()
            raw["keyboard_hand"] = "Left" if mouse_hand == "Right" else "Right"
            raw["swap_hands"] = self.swap_hands.isChecked()
            raw["monitor_mode"] = self.monitor_mode.currentText()
            raw["fixed_monitor"] = int(self.fixed_monitor.currentData() or 0)
            arming = raw.setdefault("arming", {})
            arming["enabled"] = False
            arming["hold_seconds"] = self.arm_hold.value()
            arming["release_frames"] = self.arm_release_frames.value()
            arming["cooldown_seconds"] = self.arm_cooldown.value()
            arming["auto_disarm_on_hand_loss_seconds"] = self.auto_disarm.value()
            thresholds = raw.setdefault("thresholds", {})
            thresholds["cursor_smoothing"] = self.smoothing.value()
            thresholds["cursor_adaptive_smoothing"] = self.adaptive_smoothing.isChecked()
            thresholds["pinch_confirm_seconds"] = self.pinch_confirm.value()
            thresholds['pinch_release_seconds'] = self.pinch_release.value()
            thresholds["cursor_deadzone_px"] = self.deadzone.value()
            thresholds["scroll_sensitivity"] = self.scroll.value()
            thresholds["monitor_edge_switch_enabled"] = self.edge_switch.isChecked()
            thresholds["monitor_edge_dwell_seconds"] = self.edge_dwell.value()
            thresholds["monitor_edge_zone"] = self.edge_zone.value() / 100
            thresholds["gesture_confidence"] = self.gesture_confidence.value()
            thresholds["gesture_on_frames"] = self.gesture_on_frames.value()
            thresholds["pinch_close_ratio"] = self.pinch_close.value()
            thresholds["pinch_open_ratio"] = self.pinch_open.value()
            thresholds["drag_hold_seconds"] = self.drag_hold.value()
            thresholds["scroll_deadzone"] = self.scroll_deadzone.value()
            thresholds["mouse_move_gesture"] = self.mouse_move_gesture.currentData()
            thresholds["mouse_primary_click_gesture"] = self.mouse_primary_click.currentData()
            thresholds["mouse_secondary_click_gesture"] = self.mouse_secondary_click.currentData()
            thresholds["mouse_scroll_gesture"] = self.mouse_scroll_gesture.currentData()
            if thresholds["pinch_close_ratio"] >= thresholds["pinch_open_ratio"]:
                raise ValueError(
                    "Pinch start ratio must be lower than Pinch release ratio")
            primary = thresholds["mouse_primary_click_gesture"]
            secondary = thresholds["mouse_secondary_click_gesture"]
            if primary != "disabled" and primary == secondary:
                raise ValueError(
                    "Primary and secondary click gestures must be different")
            move = thresholds["mouse_move_gesture"]
            if move != "any" and move == thresholds["mouse_scroll_gesture"]:
                raise ValueError("Move pointer and Scroll must use different poses")
            selections = {gesture: (action.currentText(), keys.text())
                          for gesture, (action, keys) in self.gesture_rows.items()}
            raw = apply_gesture_bindings(raw, selections)
            raw['gesture_v1'] = self.v1_panel.value()
            save_user_profile(USER_PROFILE, raw)
            save_desktop_settings(APP_SETTINGS, DesktopSettings(
                self.camera.value(), self.start_paused.isChecked(),
                self.show_skeleton.isChecked(), self.show_guide.isChecked()))
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
