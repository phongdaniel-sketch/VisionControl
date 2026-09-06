"""Settings editor for versioned Gesture Hand controls."""
from PySide6.QtWidgets import QWidget, QFormLayout, QCheckBox, QDoubleSpinBox, QLabel, QLineEdit, QComboBox, QHBoxLayout
from .gesture_v1_config import config, DEFAULTS, SYMBOLS, CORNERS


class GestureV1Panel(QWidget):
    def __init__(self, raw):
        super().__init__()
        self.form = QFormLayout(self)
        self.controls = {}; self.bindings = {}; self.actions = {}
        note = QLabel('Configure gestures for both palm and fingertip control.\n'
                      'Zoom uses application shortcuts; support varies by application.\n'
                      'Scroll and symbols take priority over clicks. Assigned OK reserves its pose from drag.')
        note.setWordWrap(True); self.form.addRow(note)
        for key, title in [('two_hands', 'Enable second hand'),
                           ('fist_switch', 'Right fist 3 s toggles second hand'),
                           ('scroll', 'Vertical / horizontal scroll'), ('zoom', 'Zoom gestures'),
                           ('volume', 'Volume rotation'), ('reverse_scroll', 'Reverse scroll')]:
            control = QCheckBox(); self.controls[key] = control; self.form.addRow(title, control)
        for key, title, lo, hi, step in [
            ('modifier_seconds', 'Ctrl / Shift / Alt confirmation (s)', .3, 3, .1),
            ('pose_seconds', 'Pose confirmation (s)', .1, 1, .05),
            ('symbol_seconds', 'Symbol confirmation (s)', .2, 2, .1),
            ('corner_seconds', 'Double fist window (s)', 1, 5, .5),
            ('scroll_speed', 'Scroll sensitivity', 1, 150, 1),
            ('close_spread', 'Closed finger spacing', .15, .8, .05),
            ('wide_spread', 'Wide finger spacing', .3, 1.5, .05)]:
            control = QDoubleSpinBox(); control.setRange(lo, hi); control.setSingleStep(step)
            control.setDecimals(2); self.controls[key] = control; self.form.addRow(title, control)
        self.form.addRow(QLabel('Second hand: Ctrl = fist; Shift = fingers together; Alt = pinch.'))
        for count in '12345':
            row = QWidget(); layout = QHBoxLayout(row); layout.setContentsMargins(0, 0, 0, 0)
            kind = QComboBox(); kind.addItems(['Disabled', 'Press', 'Hold'])
            keys = QLineEdit(); keys.setPlaceholderText('e.g. r or ctrl+c')
            layout.addWidget(kind); layout.addWidget(keys)
            self.bindings[count] = (kind, keys); self.form.addRow(f'{count} fingers', row)
        help_text = QLabel('Actions: leave blank, key chord (ctrl+c), volume_up, volume_down, mute, zoom_in, zoom_out.\n'
                          'Corners use the selected display. Fist → open twice; leaving the corner cancels.')
        help_text.setWordWrap(True); self.form.addRow(help_text)
        for group, names in [('symbols', SYMBOLS), ('corners', CORNERS)]:
            for name in names:
                edit = QLineEdit(); edit.setPlaceholderText('Not assigned')
                self.actions[group, name] = edit; self.form.addRow(name.replace('_', ' ').title(), edit)
        self.load(raw)

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
