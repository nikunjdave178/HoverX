from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect, QPropertyAnimation
from PyQt6.QtGui import QPainter, QColor

class FloatingWidget(QWidget):
    ICON_SIZE = 56
    EXPANDED_WIDTH = 280
    EXPANDED_HEIGHT = 140

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setMouseTracking(True)

        self.resize(self.ICON_SIZE, self.ICON_SIZE)

        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(180)

    # ---------- Paint ----------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.width() == self.ICON_SIZE:
            painter.setBrush(QColor(32, 32, 32, 230))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, self.ICON_SIZE, self.ICON_SIZE)

            painter.setPen(QColor(240, 240, 240))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "♪")
        else:
            painter.setBrush(QColor(28, 28, 28, 240))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect(), 12, 12)

    # ---------- Hover ----------
    def enterEvent(self, event):
        if self.width() == self.ICON_SIZE:
            self.expand()

    def leaveEvent(self, event):
        if self.width() != self.ICON_SIZE:
            self.collapse()

    # ---------- Animation ----------
    def expand(self):
        start = self.geometry()
        end = QRect(
            start.x(),
            start.y(),
            self.EXPANDED_WIDTH,
            self.EXPANDED_HEIGHT,
        )
        self._animate(start, end)

    def collapse(self):
        start = self.geometry()
        end = QRect(
            start.x(),
            start.y(),
            self.ICON_SIZE,
            self.ICON_SIZE,
        )
        self._animate(start, end)

    def _animate(self, start, end):
        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.start()
