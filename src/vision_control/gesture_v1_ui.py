"""Settings editor for versioned Gesture Hand controls."""
from PySide6.QtWidgets import QWidget, QFormLayout, QDoubleSpinBox, QLabel, QLineEdit, QComboBox, QHBoxLayout, QVBoxLayout, QTabWidget, QGroupBox
from .settings_widgets import StateCheckBox as QCheckBox, ActionPicker
from .gesture_v1_config import config, DEFAULTS, SYMBOLS, CORNERS


class GestureV1Panel(QWidget):
    def __init__(self, raw, pinch_rows=()):
        super().__init__()
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.form = self.section('Controls')
        self.controls = {}; self.bindings = {}; self.actions = {}
        note = QLabel('Turn gestures on or off. The same choices apply to both pointer modes.')
        note.setWordWrap(True); self.form.addRow(note)
        for key, title in [('two_hands', 'Enable second hand'),
                           ('fist_switch', 'Right fist 3 s toggles second hand'),
                           ('scroll', 'Vertical / horizontal scroll'), ('zoom', 'Zoom gestures'),
                           ('volume', 'Volume rotation'), ('reverse_scroll', 'Reverse scroll')]:
            control = QCheckBox(); self.controls[key] = control; self.form.addRow(title, control)
        self.form = self.section('Fine tuning')
        tuning = self.form
        note = QLabel('Adjust one value at a time. Times are in seconds; finger spacing is relative to hand size.')
        note.setWordWrap(True); self.form.addRow(note)
        def group(title):
            box = QGroupBox(title)
            form = QFormLayout(box)
            form.setVerticalSpacing(10)
            tuning.addRow(box)
            return form
        clicks = group('Click && Drag')
        for title, widget in pinch_rows:
            clicks.addRow(title, widget)
        note = QLabel('Pinch starts drag after the confirmation time. Open thumb/index to release. Curl clicks keep their existing timing.')
        note.setWordWrap(True); clicks.addRow(note)
        motion = group('Scroll / Zoom / Volume')
        keys = group('Keys && Symbols')
        for key, title, lo, hi, step in [
            ('modifier_seconds', 'Ctrl / Shift / Alt confirmation (s)', .3, 3, .1),
            ('pose_seconds', 'Pose confirmation (s) · also applies to motion gestures', .1, 1, .05),
            ('symbol_seconds', 'Symbol confirmation (s)', .2, 2, .1),
            ('corner_seconds', 'Double fist window (s)', 1, 5, .5),
            ('scroll_speed', 'Scroll sensitivity', 1, 150, 1),
            ('close_spread', 'Closed finger spacing', .15, .8, .05),
            ('wide_spread', 'Wide finger spacing', .3, 1.5, .05)]:
            control = QDoubleSpinBox(); control.setRange(lo, hi); control.setSingleStep(step)
            control.setDecimals(2); control.setMaximumWidth(180)
            self.controls[key] = control
            form = motion if key in ('scroll_speed', 'close_spread', 'wide_spread') else keys
            form.addRow(title, control)
        self.form = self.section('Keyboard')
        note = QLabel('Hold: fist = Ctrl; fingers together = Shift; pinch = Alt.\nChoose shortcuts for 1–5 fingers below.')
        note.setWordWrap(True); self.form.addRow(note)
        for count in '12345':
            row = QWidget(); layout = QHBoxLayout(row); layout.setContentsMargins(0, 0, 0, 0)
            kind = QComboBox(); kind.addItems(['Disabled', 'Press', 'Hold'])
            keys = QLineEdit(); keys.setPlaceholderText('e.g. r or ctrl+c')
            layout.addWidget(kind); layout.addWidget(keys)
            self.bindings[count] = (kind, keys); self.form.addRow(f'{count} fingers', row)
        self.form = self.section('Actions')
        help_text = QLabel('Choose an action or type a shortcut, e.g. ctrl+c. OK uses three extended fingers; this pose will not start a drag when assigned.\n'
                          'Corners use the selected display. Fist → open twice; leaving the corner cancels.')
        help_text.setWordWrap(True); self.form.addRow(help_text)
        for group, names in [('symbols', SYMBOLS), ('corners', CORNERS)]:
            for name in names:
                edit = ActionPicker()
                self.actions[group, name] = edit; self.form.addRow(name.replace('_', ' ').title(), edit)
        self.load(raw)
        self.tabs.tabBar().moveTab(1, 3)

    def section(self, name):
        page = QWidget()
        form = QFormLayout(page)
        form.setVerticalSpacing(12)
        form.setHorizontalSpacing(20)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.tabs.addTab(page, name)
        return form

    def load(self, raw):
        cfg = config(raw)
        for key, control in self.controls.items():
            if isinstance(control, QCheckBox): control.setChecked(cfg[key])
            else: control.setValue(cfg[key])
        for count, (kind, keys) in self.bindings.items():
            binding = cfg['bindings'].get(count, {})
            kind.setCurrentText(binding.get('type', 'disabled').title())
            keys.setText(binding.get('keys', ''))
        for (group, name), edit in self.actions.items():
            edit.setText(cfg[group].get(name, ''))

    def value(self):
        result = {'version': 1, 'enabled': True, 'bindings': {}, 'symbols': {}, 'corners': {}}
        for key, control in self.controls.items():
            result[key] = control.isChecked() if isinstance(control, QCheckBox) else control.value()
        for count, (kind, keys) in self.bindings.items():
            if kind.currentText() != 'Disabled':
                result['bindings'][count] = {'type': kind.currentText().lower(), 'keys': keys.text().strip().lower()}
        for (group, name), edit in self.actions.items():
            if edit.text().strip(): result[group][name] = edit.text().strip().lower()
        return config(result)
