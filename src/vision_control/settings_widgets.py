"""Accessible settings controls with explicit state and named actions."""
from PySide6.QtWidgets import QCheckBox, QComboBox


class StateCheckBox(QCheckBox):
    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self.label = text
        self.toggled.connect(self._refresh)
        self._refresh()

    def _refresh(self, *_):
        state = 'On' if self.isChecked() else 'Off'
        super().setText(f'{state}  ·  {self.label}' if self.label else state)
        self.setAccessibleName(f'{self.label}: {state}' if self.label else state)


class ActionPicker(QComboBox):
    def __init__(self):
        super().__init__()
        self.setEditable(True)
        self.setMinimumWidth(240)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        for label, value in [('Not assigned', ''), ('Volume up', 'volume_up'),
                             ('Volume down', 'volume_down'), ('Mute / unmute', 'mute'),
                             ('Zoom in', 'zoom_in'), ('Zoom out', 'zoom_out'),
                             ('Copy', 'ctrl+c'), ('Paste', 'ctrl+v'),
                             ('Voice Listen Toggle', 'voice_listen_toggle'),
                             ('Play / Pause', 'play_pause'), ('Next Track', 'next_track'),
                             ('Previous Track', 'previous_track'), ('Show Desktop', 'win+d'),
                             ('Task View', 'win+tab'), ('Screenshot', 'win+shift+s'),
                             ('Open This PC', 'open_computer'), ('Undo', 'ctrl+z'),
                             ('Redo', 'ctrl+y'), ('Escape', 'esc'),
                             ('Pause Gesture Control', 'pause_gestures')]:
            self.addItem(label, value)
        self.lineEdit().setPlaceholderText('Choose an action or type a shortcut')
        self.setToolTip('Choose an action, or type a shortcut such as ctrl+c or win+d.')

    def text(self):
        if self.currentIndex() >= 0 and self.currentText() == self.itemText(self.currentIndex()):
            return self.currentData()
        return self.currentText()

    def setText(self, text):
        index = self.findData(text)
        if index >= 0:
            self.setCurrentIndex(index)
        else:
            self.setCurrentIndex(-1)
            self.setEditText(text)
