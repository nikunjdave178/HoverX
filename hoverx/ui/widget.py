import time
from PyQt6.QtWidgets import QWidget,QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QRect, QPropertyAnimation, QSize, QTimer
from PyQt6.QtGui import QPainter, QColor, QFontMetrics
from hoverx.ui.icons import svg_to_icon

PLAY_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="white" class="bi bi-play-fill" viewBox="0 0 16 16">
  <path d="m11.596 8.697-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393"/>
</svg>
"""

PAUSE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="white" class="bi bi-pause-fill" viewBox="0 0 16 16">
  <path d="M5.5 3.5A1.5 1.5 0 0 1 7 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5m5 0A1.5 1.5 0 0 1 12 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5"/>
</svg>
"""

NEXT_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="white" class="bi bi-fast-forward-fill" viewBox="0 0 16 16">
  <path d="M7.596 7.304a.802.802 0 0 1 0 1.392l-6.363 3.692C.713 12.69 0 12.345 0 11.692V4.308c0-.653.713-.998 1.233-.696z"/>
  <path d="M15.596 7.304a.802.802 0 0 1 0 1.392l-6.363 3.692C8.713 12.69 8 12.345 8 11.692V4.308c0-.653.713-.998 1.233-.696z"/>
</svg>
"""

PREV_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="white" class="bi bi-fast-forward-fill" viewBox="0 0 16 16">
  <g transform="rotate(180 8 8)">
    <path d="M7.596 7.304a.802.802 0 0 1 0 1.392l-6.363 3.692C.713 12.69 0 12.345 0 11.692V4.308c0-.653.713-.998 1.233-.696z"/>
    <path d="M15.596 7.304a.802.802 0 0 1 0 1.392l-6.363 3.692C8.713 12.69 8 12.345 8 11.692V4.308c0-.653.713-.998 1.233-.696z"/>
  </g>
</svg>
"""


class FloatingWidget(QWidget):
    ICON_SIZE = 56
    EXPANDED_WIDTH = 280
    EXPANDED_HEIGHT = 140

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        self._raw_title = ""
        self._raw_artist = ""
        self._manual_toggle_ts = 0.0

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
        self._anim.setDuration(100)

        # Content container
        self.content_widget = QWidget(self)
        self.content_widget.setGeometry(0, 0, self.EXPANDED_WIDTH, self.EXPANDED_HEIGHT)
        self.content_widget.setStyleSheet(
            "background: rgba(28,28,28,240); border-radius: 12px;"
        )
        self.content_widget.hide()
        self.content_widget.setMouseTracking(True)

        self._dragging = False
        self._drag_offset = None
        self.content_widget.installEventFilter(self)

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
        self.title_label = QLabel("")
        self.title_label.setStyleSheet("color: white; font-size: 14px;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.title_label.setWordWrap(False)

        self.artist_label = QLabel("")
        self.artist_label.setStyleSheet("color: #CFCFCF; font-size: 12px;")
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.artist_label.setWordWrap(False)

        layout.addSpacing(6)
        layout.addWidget(self.title_label)
        layout.addWidget(self.artist_label)

        # ---------- Track info update ----------
        self.track_timer = QTimer(self)
        self.track_timer.setInterval(1000)  # 1 second
        self.track_timer.timeout.connect(self.update_track_info)
        self.track_timer.start()

        self.play_btn.clicked.connect(self._on_play_clicked)
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
        if not self.rect().contains(self.mapFromGlobal(self.cursor().pos())):
            self.collapse()

    # ---------- Expand / Collapse ----------
    def expand(self):
        if self.width() != self.ICON_SIZE:
            return
        self.content_widget.show()
        self._animate_to(
            QRect(self.x(), self.y(), self.EXPANDED_WIDTH, self.EXPANDED_HEIGHT)
        )

    def collapse(self):
        if self.width() == self.ICON_SIZE:
            return
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
        self._update_labels()

    def update_track_info(self):
        now = time.perf_counter()

        # skip reconciliation shortly after manual click
        if now - self._manual_toggle_ts < 0.4:
            return
        
        title, artist = self.controller.get_track_info()
        playing = self.controller.is_playing()

        self._update_labels()

        icon_svg = PAUSE_SVG if playing else PLAY_SVG
        self.play_btn.setIcon(svg_to_icon(icon_svg, QSize(32, 32)))

    def _update_labels(self):
        if self._raw_title and self.title_label.width() > 0:
            metrics = QFontMetrics(self.title_label.font())
            elided = metrics.elidedText(
                self._raw_title,
                Qt.TextElideMode.ElideRight,
                self.title_label.width()
            )
            self.title_label.setText(elided)

        if self._raw_artist and self.artist_label.width() > 0:
            metrics = QFontMetrics(self.artist_label.font())
            elided = metrics.elidedText(
                self._raw_artist,
                Qt.TextElideMode.ElideRight,
                self.artist_label.width()
            )
            self.artist_label.setText(elided)

    # ---------- Dragging ----------
    def eventFilter(self, obj, event):
        if obj is self.content_widget:
            if event.type() == event.Type.MouseButtonPress:
                if event.buttons() & Qt.MouseButton.LeftButton:
                    # prevent dragging when clicking buttons
                    if self.content_widget.childAt(event.position().toPoint()):
                        return False

                    self._dragging = True
                    self._drag_offset = (
                        event.globalPosition().toPoint()
                        - self.frameGeometry().topLeft()
                    )
                    return True

            elif event.type() == event.Type.MouseMove:
                if self._dragging:
                    self.move(
                        event.globalPosition().toPoint()
                        - self._drag_offset
                    )
                    return True

            elif event.type() == event.Type.MouseButtonRelease:
                if self._dragging:
                    self._dragging = False
                    return True

        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def _on_play_clicked(self):
        self._manual_toggle_ts = time.perf_counter()

        # optimistic update
        currently_playing = self.controller.is_playing()
        self.play_btn.setIcon(
            self._icon_pause if not currently_playing else self._icon_play
        )

        self.controller.play_pause()




