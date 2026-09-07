"""Camera names in the same backend/index order used for capture."""
import sys
from PySide6.QtWidgets import QComboBox


def camera_devices():
    import cv2
    from cv2_enumerate_cameras import enumerate_cameras
    backend = cv2.CAP_DSHOW if sys.platform == 'win32' else cv2.CAP_AVFOUNDATION if sys.platform == 'darwin' else cv2.CAP_V4L2
    return [(c.index, c.name) for c in enumerate_cameras(backend)]


class CameraPicker(QComboBox):
    def __init__(self, selected=0):
        super().__init__()
        self.setMinimumWidth(300)
        self.error = ''
        self.refresh(selected)

    def value(self):
        return int(self.currentData() or 0)

    def setValue(self, value):
        index = self.findData(value)
        if index < 0:
            self.addItem(f'Camera {value} · not currently listed', value)
            index = self.count()-1
        self.setCurrentIndex(index)

    def refresh(self, selected=None):
        selected = self.value() if selected is None else selected
        self.clear()
        self.error = ''
        try:
            for index, name in camera_devices():
                self.addItem(f'{name} · Camera {index}', index)
        except Exception as exc:
            self.error = str(exc)
        self.setValue(selected)
