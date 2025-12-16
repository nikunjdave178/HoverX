from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor

class FloatingWidget(QWidget):
    ICON_SIZE = 56

    def __init__(self):
        super().__init__()
        
        # Window Behavior
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setFixedSize(self.ICON_SIZE, self.ICON_SIZE)
        
        # Fixed Size
        self.resize(200, 100)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # BG Circle
        painter.setBrush(QColor(32,32,32,230))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.ICON_SIZE, self.ICON_SIZE)   

        # Temp Glyph
        painter.setPen(QColor(240, 240, 240))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "♪")
