"""Desktop tray UI; input and camera ownership stay with the Controller."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


class ControllerTray:
    def __init__(self, window):
        self.window = window
        self.icon = QSystemTrayIcon(window)
        self.menu = QMenu(window)
        self.state_action = self.menu.addAction('VisionControl · Paused')
        self.state_action.setEnabled(False)
        self.menu.addSeparator()
        self.menu.addAction('Open Controller', window.show_controller)
        self.toggle_action = self.menu.addAction('Start', window.toggle_pause)
        self.settings_action = self.menu.addAction('Settings', self.open_settings)
        self.menu.addSeparator()
        self.menu.addAction('Quit', window.quit_application)
        self.icon.setContextMenu(self.menu)
        self.icon.activated.connect(self.activated)
        self.menu.aboutToShow.connect(self.refresh)
        self.state = None
        self.refresh()
        self.icon.show()

    def available(self):
        return self.icon.isVisible() and QSystemTrayIcon.isSystemTrayAvailable()

    def activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger,
                      QSystemTrayIcon.ActivationReason.DoubleClick):
            self.window.show_controller()

    def open_settings(self):
        self.window.show_controller()
        self.window.open_settings()
        self.refresh()

    def refresh(self):
        w = self.window
        state = 'Error' if w.frame_error is not None else 'Paused' if w.runtime.paused else 'Active'
        self.toggle_action.setText('Start' if w.runtime.paused else 'Pause')
        self.toggle_action.setEnabled(w.can_toggle_input())
        self.settings_action.setEnabled(not w.closing and w.diagnostic_window is None)
        if self.state == state:
            return
        self.state = state
        self.state_action.setText(f'VisionControl · {state}')
        self.icon.setToolTip(f'VisionControl · {state}')
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(QColor({'Active': '#238b45', 'Paused': '#245db5', 'Error': '#bd392f'}[state]))
        painter.drawEllipse(2, 2, 28, 28)
        painter.setBrush(Qt.GlobalColor.white)
        if state == 'Paused':
            painter.drawRect(11, 10, 3, 12)
            painter.drawRect(18, 10, 3, 12)
        elif state == 'Error':
            painter.drawRect(15, 8, 2, 10)
            painter.drawEllipse(15, 22, 2, 2)
        else:
            from PySide6.QtGui import QPolygon
            from PySide6.QtCore import QPoint
            painter.drawPolygon(QPolygon([QPoint(12, 8), QPoint(24, 16), QPoint(12, 24)]))
        painter.end()
        self.icon.setIcon(QIcon(pixmap))
