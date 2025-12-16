from PyQt6.QtWidgets import QWidget,QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QRect, QPropertyAnimation, QSize, QTimer
from PyQt6.QtGui import QPainter, QColor
from hoverx.ui.icons import svg_to_icon

PLAY_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M30 25 L30 75 L65 50 Z" fill="#00FFFF"/>
</svg>
"""

PAUSE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="40" y="25" width="6" height="50" fill="#00FFFF"/>
  <rect x="60" y="25" width="6" height="50" fill="#00FFFF"/>
</svg>
"""

NEXT_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M30 25 L30 75 L65 50 Z" fill="#00FFFF"/>
  <rect x="68" y="25" width="6" height="50" fill="#00FFFF"/>
</svg>
"""

PREV_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M70 25 L70 75 L35 50 Z" fill="#00FFFF"/>
  <rect x="26" y="25" width="6" height="50" fill="#00FFFF"/>
</svg>
"""


class FloatingWidget(QWidget):
    ICON_SIZE = 56
    EXPANDED_WIDTH = 280
    EXPANDED_HEIGHT = 140

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

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

        # ---------- Layout ----------
        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # Controls row
        controls = QHBoxLayout()
        controls.addStretch()

        self.prev_btn = QPushButton()
        self.play_btn = QPushButton()
        self.next_btn = QPushButton()

        self.prev_btn.setIcon(svg_to_icon(PREV_SVG, QSize(32, 32)))
        self.play_btn.setIcon(svg_to_icon(PLAY_SVG, QSize(32, 32)))
        self.next_btn.setIcon(svg_to_icon(NEXT_SVG, QSize(32, 32)))

        for btn in (self.prev_btn, self.play_btn, self.next_btn):
            btn.setFixedSize(60, 40)
            btn.setIconSize(QSize(32, 32))
            btn.setStyleSheet(
                "QPushButton { background: rgba(255,255,255,0.08); border-radius: 8px; }"
                "QPushButton:hover { background: rgba(255,255,255,0.16); }"
            )
            controls.addWidget(btn)

        controls.addStretch()
        layout.addLayout(controls)

        # Labels
        self.title_label = QLabel("Track Title")
        self.title_label.setStyleSheet("color: white; font-size: 14px;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.artist_label = QLabel("Artist Name")
        self.artist_label.setStyleSheet("color: #CFCFCF; font-size: 12px;")
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(6)
        layout.addWidget(self.title_label)
        layout.addWidget(self.artist_label)

        # ---------- Track info update ----------
        self.track_timer = QTimer(self)
        self.track_timer.setInterval(1000)  # 1 second
        self.track_timer.timeout.connect(self.update_track_info)
        self.track_timer.start()

        self.play_btn.clicked.connect(self.controller.play_pause)
        self.next_btn.clicked.connect(self.controller.next)
        self.prev_btn.clicked.connect(self.controller.previous)

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

    def update_track_info(self):
        title, artist = self.controller.get_track_info()
        if title:
            self.title_label.setText(title)
        if artist:
            self.artist_label.setText(artist)


        # Sync play / pause icon
        playing = self.controller.is_playing()
        icon_svg = PAUSE_SVG if playing else PLAY_SVG
        self.play_btn.setIcon(svg_to_icon(icon_svg, QSize(32, 32)))

