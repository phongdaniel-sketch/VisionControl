import unittest
from types import SimpleNamespace
from PySide6.QtWidgets import QApplication, QSizePolicy
from vision_control.diagnostics_ui import DiagnosticWindow


class DiagnosticWindowSizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_default_size_fits_screen_and_preview_does_not_force_growth(self):
        window = DiagnosticWindow(SimpleNamespace(debug_enabled=False), autostart=False)
        available = window.screen().availableGeometry()
        self.assertEqual(window.width(), min(1200, int(available.width() * .9)))
        self.assertEqual(window.height(), min(760, int(available.height() * .9)))
        self.assertEqual(window.preview.sizePolicy().horizontalPolicy(), QSizePolicy.Policy.Ignored)
        window.resize(700, 500)
        window.layout().activate()
        self.assertLessEqual(window.stop_button.geometry().bottom(), window.height())
        self.assertLessEqual(window.preview.geometry().right(), window.width())
        window.deleteLater()
