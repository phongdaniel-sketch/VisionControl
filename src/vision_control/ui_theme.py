from .paths import resource_root


_ASSET_ROOT = (resource_root() / "assets" / "ui").as_posix()

_APP_STYLE_TEMPLATE = """
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
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { min-height: 36px; padding: 0 12px; background: #111c2d; color: #f4f7fc; border: 1px solid #49617f; border-radius: 7px; selection-background-color: #246bff; }
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover { background: #142238; border-color: #6785ad; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { background: #142238; border: 2px solid #3478ff; }
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled { background: #0a111d; color: #718097; border-color: #26364d; }
QComboBox { padding-right: 38px; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 32px; background: #1b2b43; border-left: 1px solid #49617f; border-top-right-radius: 6px; border-bottom-right-radius: 6px; }
QComboBox::drop-down:hover { background: #245caa; }
QComboBox::down-arrow { image: url("__DOWN_ARROW__"); width: 12px; height: 12px; }
QComboBox QAbstractItemView { background: #101a2a; color: #f4f7fc; border: 1px solid #56739a; selection-background-color: #1d5fd1; selection-color: #ffffff; outline: 0; padding: 4px; }
QSpinBox, QDoubleSpinBox { padding-right: 38px; }
QSpinBox::up-button, QDoubleSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right; width: 30px; background: #1b2b43; border-left: 1px solid #49617f; border-bottom: 1px solid #344967; border-top-right-radius: 6px; }
QSpinBox::down-button, QDoubleSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right; width: 30px; background: #1b2b43; border-left: 1px solid #49617f; border-top: 1px solid #344967; border-bottom-right-radius: 6px; }
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background: #245caa; }
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow { image: url("__UP_ARROW__"); width: 12px; height: 12px; }
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow { image: url("__DOWN_ARROW__"); width: 12px; height: 12px; }
QCheckBox { spacing: 9px; }
QCheckBox { min-height: 32px; color: #f4f7fc; }
QCheckBox::indicator { width: 44px; height: 24px; }
QCheckBox::indicator:unchecked { image: url("__SWITCH_OFF__"); }
QCheckBox::indicator:checked { image: url("__SWITCH_ON__"); }
QCheckBox:disabled { color: #7f8da2; }
QTabWidget::pane { border: 1px solid #34465e; border-radius: 8px; padding: 12px; }
QTabBar::tab { background: #172235; color: #c0cddd; padding: 10px 16px; margin-right: 4px; border-bottom: 3px solid transparent; }
QTabBar::tab:selected { background: #174b9c; color: white; border-bottom: 3px solid #8bc4ff; }
QScrollArea { border: 0; background: transparent; }
QScrollBar:vertical { background: #080e18; width: 10px; }
QScrollBar::handle:vertical { background: #2a374a; border-radius: 5px; min-height: 30px; }
QStatusBar { color: #9aa6b7; }
QToolTip { background: #111a29; color: #ffffff; border: 1px solid #33445e; }
"""

APP_STYLE = (_APP_STYLE_TEMPLATE
             .replace("__SWITCH_ON__", f"{_ASSET_ROOT}/switch-on.svg")
             .replace("__SWITCH_OFF__", f"{_ASSET_ROOT}/switch-off.svg")
             .replace("__UP_ARROW__", f"{_ASSET_ROOT}/chevron-up.svg")
             .replace("__DOWN_ARROW__", f"{_ASSET_ROOT}/chevron-down.svg"))

GESTURE_LABELS = {
    "point": "Point", "peace": "Peace", "three_fingers": "Three fingers",
    "four_fingers": "Four fingers", "open_palm": "Open palm",
    "fist": "Fist", "pinch": "Pinch",
}


def humanize(value: str) -> str:
    return GESTURE_LABELS.get(value, value.replace("_", " ").title())
