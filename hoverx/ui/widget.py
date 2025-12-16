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

        # Geometry animation
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(180)

        # Content container
        self.content_widget = QWidget(self)
        self.content_widget.setGeometry(0, 0, self.EXPANDED_WIDTH, self.EXPANDED_HEIGHT)
        self.content_widget.setStyleSheet(
            "background: rgba(28,28,28,240); border-radius: 12px;"
        )
        self.content_widget.hide()
        self.content_widget.setMouseTracking(True)

    # ---------- Paint (collapsed only) ----------
    def paintEvent(self, event):
        if self.width() == self.ICON_SIZE:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            painter.setBrush(QColor(32, 32, 32, 230))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, self.ICON_SIZE, self.ICON_SIZE)

            painter.setPen(QColor(240, 240, 240))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "♪")

    # ---------- Hover ----------
    def enterEvent(self, event):
        if self.width() == self.ICON_SIZE:
            self.expand()

    def leaveEvent(self, event):
        # IMPORTANT: check global cursor position
        if not self.geometry().contains(self.mapFromGlobal(self.cursor().pos())):
            self.collapse()

    # ---------- Expand / Collapse ----------
    def expand(self):
        self.content_widget.show()
        self._animate_to(
            QRect(self.x(), self.y(), self.EXPANDED_WIDTH, self.EXPANDED_HEIGHT)
        )

    def collapse(self):
        def on_finished():
            try:
                self._anim.finished.disconnect(on_finished)
            except Exception:
                pass
            self.content_widget.hide()
            self.update()

        self._anim.finished.connect(on_finished)
        self._animate_to(
            QRect(self.x(), self.y(), self.ICON_SIZE, self.ICON_SIZE)
        )

    def _animate_to(self, rect):
        self._anim.stop()
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(rect)
        self._anim.start()

    # ---------- Keep content synced ----------
    def resizeEvent(self, event):
        self.content_widget.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)
