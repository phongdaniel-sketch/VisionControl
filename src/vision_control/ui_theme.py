APP_STYLE = """
QWidget { background: #070c16; color: #e8edf7; font-family: "Inter", "SF Pro Text", "Segoe UI"; font-size: 13px; }
QLabel, QCheckBox { background: transparent; }
QMainWindow, QDialog { background: #050914; }
QFrame#card, QGroupBox { background: #0c1320; border: 1px solid #202b3d; border-radius: 12px; }
QGroupBox { margin-top: 12px; padding: 18px 14px 14px 14px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; color: #f4f7fc; }
QLabel#muted { color: #8e9bad; }
QLabel#sectionTitle { font-size: 16px; font-weight: 700; }
QLabel#brand { font-size: 20px; font-weight: 800; letter-spacing: 2px; }
QLabel#metric { color: #46a0ff; font-weight: 700; }
QPushButton { min-height: 38px; padding: 0 16px; border: 1px solid #26344a; border-radius: 8px; background: #101827; color: #eef3fb; font-weight: 600; }
QPushButton:hover { background: #162239; border-color: #3d5274; }
QPushButton:pressed { background: #0c1422; }
QPushButton:disabled { color: #5f6b7c; background: #0a101b; border-color: #182131; }
QPushButton#primary { background: #1557e8; border-color: #2f72ff; }
QPushButton#primary:hover { background: #2166f3; }
QPushButton#danger { background: #331718; border-color: #ff6934; color: #fff2ed; }
QPushButton#nav { text-align: left; border: 0; background: transparent; color: #aeb8c8; }
QPushButton#nav:hover { background: #111b2b; color: #ffffff; }
QPushButton#nav:checked { background: #123ca8; color: #ffffff; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { min-height: 34px; padding: 0 10px; background: #0b1220; border: 1px solid #26344a; border-radius: 7px; selection-background-color: #246bff; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #3478ff; }
QComboBox::drop-down { border: 0; width: 24px; }
QCheckBox { spacing: 9px; }
QCheckBox::indicator { width: 34px; height: 18px; }
QCheckBox::indicator:unchecked { border: 1px solid #3a4658; border-radius: 9px; background: #141c29; }
QCheckBox::indicator:checked { border: 1px solid #3478ff; border-radius: 9px; background: #246bff; }
QScrollArea { border: 0; background: transparent; }
QScrollBar:vertical { background: #080e18; width: 10px; }
QScrollBar::handle:vertical { background: #2a374a; border-radius: 5px; min-height: 30px; }
QStatusBar { color: #9aa6b7; }
QToolTip { background: #111a29; color: #ffffff; border: 1px solid #33445e; }
"""

GESTURE_LABELS = {
    "point": "Point", "peace": "Peace", "three_fingers": "Three fingers",
    "four_fingers": "Four fingers", "open_palm": "Open palm",
    "fist": "Fist", "pinch": "Pinch",
}


def humanize(value: str) -> str:
    return GESTURE_LABELS.get(value, value.replace("_", " ").title())
