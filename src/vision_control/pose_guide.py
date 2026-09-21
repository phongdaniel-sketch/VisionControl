"""Vietnamese calibration steps and schematic examples, separate from tracking."""
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


GUIDE = {
    'open': ('M\u1edf ng\u00f3n c\u00e1i, du\u1ed7i ng\u00f3n tr\u1ecf v\u00e0 gi\u1eefa', (
        'Du\u1ed7i ng\u00f3n tr\u1ecf (v\u00e0ng) v\u00e0 ng\u00f3n gi\u1eefa (xanh l\u00e1).',
        'M\u1edf ng\u00f3n c\u00e1i (xanh cyan) ra xa l\u00f2ng b\u00e0n tay, kh\u00f4ng ch\u1ea1m ng\u00f3n tr\u1ecf.',
        'B\u1ea5m Thu m\u1eabu, \u0111\u01b0a tay v\u00e0o v\u1ecb tr\u00ed trong 3 gi\u00e2y, r\u1ed3i gi\u1eef y\u00ean \u0111\u1ebfn khi b\u00e1o \u0111\u00e3 thu.')),
    'tucked': ('Thu ng\u00f3n c\u00e1i v\u00e0o l\u00f2ng b\u00e0n tay', (
        'Gi\u1eef ng\u00f3n tr\u1ecf v\u00e0 ng\u00f3n gi\u1eefa du\u1ed7i th\u1eb3ng nh\u01b0 b\u01b0\u1edbc tr\u01b0\u1edbc.',
        'Thu ri\u00eang ng\u00f3n c\u00e1i v\u00e0o s\u00e1t l\u00f2ng b\u00e0n tay; kh\u00f4ng ch\u1ee5m hai \u0111\u1ea7u ng\u00f3n \u0111\u1ec3 pinch.',
        'B\u1ea5m Thu m\u1eabu v\u00e0 gi\u1eef nguy\u00ean t\u01b0 th\u1ebf khi thanh ti\u1ebfn \u0111\u1ed9 \u0111ang ch\u1ea1y.')),
    'index': ('Ch\u1ec9 g\u1eadp ng\u00f3n tr\u1ecf', (
        'M\u1edf ng\u00f3n c\u00e1i ra ngo\u00e0i, gi\u1eef ng\u00f3n gi\u1eefa du\u1ed7i th\u1eb3ng.',
        'G\u1eadp ng\u00f3n tr\u1ecf v\u1ec1 ph\u00eda l\u00f2ng b\u00e0n tay; kh\u00f4ng g\u1eadp theo ng\u00f3n gi\u1eefa.',
        'B\u1ea5m Thu m\u1eabu. Gi\u1eef ng\u00f3n tr\u1ecf \u0111ang g\u1eadp, ch\u01b0a du\u1ed7i ra trong l\u00fac thu.')),
    'middle': ('Ch\u1ec9 g\u1eadp ng\u00f3n gi\u1eefa', (
        'M\u1edf ng\u00f3n c\u00e1i ra ngo\u00e0i, gi\u1eef ng\u00f3n tr\u1ecf du\u1ed7i th\u1eb3ng.',
        'G\u1eadp ri\u00eang ng\u00f3n gi\u1eefa v\u1ec1 ph\u00eda l\u00f2ng b\u00e0n tay.',
        'B\u1ea5m Thu m\u1eabu. Gi\u1eef ng\u00f3n gi\u1eefa \u0111ang g\u1eadp, ch\u01b0a du\u1ed7i ra trong l\u00fac thu.')),
    'both': ('G\u1eadp ng\u00f3n tr\u1ecf v\u00e0 ng\u00f3n gi\u1eefa c\u00f9ng l\u00fac', (
        'Gi\u1eef ng\u00f3n c\u00e1i m\u1edf ra ngo\u00e0i, kh\u00f4ng ch\u1ea1m hai \u0111\u1ea7u ng\u00f3n c\u00f2n l\u1ea1i.',
        'G\u1eadp c\u1ea3 ng\u00f3n tr\u1ecf v\u00e0 ng\u00f3n gi\u1eefa v\u1ec1 ph\u00eda l\u00f2ng b\u00e0n tay.',
        'B\u1ea5m Thu m\u1eabu. Gi\u1eef c\u1ea3 hai ng\u00f3n \u0111ang g\u1eadp \u0111\u1ebfn khi b\u00e1o \u0111\u00e3 thu.')),
}

FINGER_NAMES = {'extended':'du\u1ed7i', 'curled':'g\u1eadp', 'unknown':'ch\u01b0a r\u00f5',
                'open':'m\u1edf', 'tucked':'thu v\u00e0o'}
BUTTON_NAMES = {'left':'tr\u00e1i', 'middle':'gi\u1eefa', 'right':'ph\u1ea3i'}


def capture_error(message):
    if 'stale' in message or 'interrupted' in message:
        return 'Camera b\u1ecb tr\u1ec5 ho\u1eb7c m\u1ea5t khung h\u00ecnh. Gi\u1eef tay trong \u1ea3nh r\u1ed3i b\u1ea5m Thu l\u1ea1i.'
    if 'unclear' in message:
        return 'Ch\u01b0a th\u1ea5y r\u00f5 tay \u0111i\u1ec1u khi\u1ec3n. \u0110\u01b0a \u0111\u1ee7 b\u00e0n tay v\u00e0o \u1ea3nh, t\u0103ng \u00e1nh s\u00e1ng r\u1ed3i b\u1ea5m Thu l\u1ea1i.'
    if 'moved' in message:
        return 'T\u01b0 th\u1ebf thay \u0111\u1ed5i qu\u00e1 nhi\u1ec1u. Gi\u1eef y\u00ean t\u1eebng ng\u00f3n trong l\u00fac thu r\u1ed3i b\u1ea5m Thu l\u1ea1i.'
    return message


def fit_error(message):
    if 'Index' in message:
        return 'M\u1eabu du\u1ed7i v\u00e0 g\u1eadp ng\u00f3n tr\u1ecf ch\u01b0a \u0111\u1ee7 kh\u00e1c bi\u1ec7t. Thu l\u1ea1i b\u1ed9 m\u1eabu v\u1edbi \u0111\u1ed9ng t\u00e1c r\u00f5 h\u01a1n.'
    if 'Middle' in message:
        return 'M\u1eabu du\u1ed7i v\u00e0 g\u1eadp ng\u00f3n gi\u1eefa ch\u01b0a \u0111\u1ee7 kh\u00e1c bi\u1ec7t. Thu l\u1ea1i b\u1ed9 m\u1eabu v\u1edbi \u0111\u1ed9ng t\u00e1c r\u00f5 h\u01a1n.'
    if 'Thumb' in message:
        return 'Ng\u00f3n c\u00e1i ch\u01b0a t\u00e1ch r\u00f5 gi\u1eefa m\u1edf v\u00e0 thu v\u00e0o. Khi g\u1eadp ng\u00f3n tr\u1ecf/gi\u1eefa, nh\u1edb gi\u1eef ng\u00f3n c\u00e1i m\u1edf.'
    return 'B\u1ed9 m\u1eabu ch\u01b0a h\u1ee3p l\u1ec7. Thu l\u1ea1i t\u1eeb \u0111\u1ea7u; c\u1ea5u h\u00ecnh c\u0169 v\u1eabn \u0111\u01b0\u1ee3c gi\u1eef nguy\u00ean.'


class PoseExample(QWidget):
    """A hand schematic; not a detector and never used as calibration data."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage = 'open'
        self.setFixedSize(190, 210)
        self.setAccessibleName('H\u00ecnh minh h\u1ecda t\u01b0 th\u1ebf b\u00e0n tay')

    def set_stage(self, stage):
        if stage != self.stage:
            self.stage = stage
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(self.width()/200, self.height()/235)
        palm = QPainterPath()
        palm.moveTo(67, 215)
        palm.lineTo(65, 165)
        palm.quadTo(43, 145, 60, 113)
        palm.quadTo(105, 95, 165, 115)
        palm.lineTo(167, 166)
        palm.quadTo(163, 190, 144, 204)
        palm.lineTo(144, 225)
        painter.setPen(QPen(QColor('#8994a5'), 2))
        painter.fillPath(palm, QColor('#283141'))
        painter.drawPath(palm)
        for name, x, top, color in (('index',77,30,'#ffe600'),
                ('middle',107,17,'#46ff46'),('ring',137,36,'#abb5c5'),('little',164,64,'#abb5c5')):
            curled = (name in ('index','middle') and self.stage in (name,'both') or
                      name == 'middle' and self.stage == 'right_contact')
            path = QPainterPath(QPointF(x,137))
            if curled:
                path.lineTo(x,95)
                path.quadTo(x+15,87,x+15,104)
                path.lineTo(x+9,148)
                tip = QPointF(x+9,148)
            else:
                path.lineTo(x,top)
                tip = QPointF(x,top)
            painter.setPen(QPen(QColor('#79889f'),12,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin))
            painter.drawPath(path)
            painter.setPen(QPen(QColor(color),3))
            painter.setBrush(QColor('#283141'))
            painter.drawEllipse(tip,5,5)
        path = QPainterPath(QPointF(68,171))
        if self.stage == 'right_contact':
            path.quadTo(70,133,116,148)
            thumb = QPointF(116,148)
        elif self.stage == 'tucked':
            path.quadTo(68,138,111,139)
            thumb = QPointF(111,139)
        else:
            path.lineTo(40,141)
            path.lineTo(23,110)
            thumb = QPointF(23,110)
        painter.setPen(QPen(QColor('#79889f'),14,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
        painter.drawPath(path)
        painter.setPen(QPen(QColor('#00dcff'),3))
        painter.drawEllipse(thumb,6,6)
        painter.end()
