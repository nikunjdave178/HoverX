from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFontMetrics

from hoverx.ui.icons import svg_to_icon
from hoverx.ui.svg_icons import PLAY_SVG, PAUSE_SVG, NEXT_SVG, PREV_SVG, VOLUME_SVG

BUTTON_STYLE = (
    "QPushButton { background: rgba(255,255,255,0.08); border-radius: 8px; }"
    "QPushButton:hover { background: rgba(255,255,255,0.16); }"
)

SLIDER_STYLE = """
QSlider::groove:horizontal {
    background: rgba(255,255,255,0.15);
    height: 4px;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background: rgba(255,255,255,0.6);
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: white;
    width: 12px;
    margin: -4px 0;
    border-radius: 6px;
}
"""


class ControlsPanel(QWidget):
    """The expanded content area: transport buttons, track labels, volume slider."""

    play_pause_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    volume_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Required for a custom QWidget *subclass* to paint its stylesheet
        # background/border at all - without this the panel stays fully
        # transparent (and, since the top-level window is a translucent
        # layered window, transparent pixels are click-through on Windows,
        # which is also why dragging silently stopped working).
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: rgba(28,28,28,240); border-radius: 12px;")
        self.setMouseTracking(True)

        self._raw_title = ""
        self._raw_artist = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # ---------- Transport controls ----------
        controls = QHBoxLayout()
        controls.addStretch()

        self.prev_btn = QPushButton()
        self.play_btn = QPushButton()
        self.next_btn = QPushButton()

        self._icon_play = svg_to_icon(PLAY_SVG, QSize(32, 32))
        self._icon_pause = svg_to_icon(PAUSE_SVG, QSize(32, 32))
        self.play_btn.setIcon(self._icon_play)

        self.prev_btn.setIcon(svg_to_icon(PREV_SVG, QSize(32, 32)))
        self.next_btn.setIcon(svg_to_icon(NEXT_SVG, QSize(32, 32)))

        for btn in (self.prev_btn, self.play_btn, self.next_btn):
            btn.setFixedSize(60, 40)
            btn.setIconSize(QSize(32, 32))
            btn.setStyleSheet(BUTTON_STYLE)
            controls.addWidget(btn)

        controls.addStretch()
        layout.addLayout(controls)

        # ---------- Labels ----------
        self.title_label = QLabel("")
        self.title_label.setStyleSheet(
            "QLabel { background: transparent; border: none; color: white; font-size: 14px; }"
        )
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.title_label.setWordWrap(False)

        self.artist_label = QLabel("")
        self.artist_label.setStyleSheet(
            "QLabel { background: transparent; border: none; color: #CFCFCF; font-size: 12px; }"
        )
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        self.artist_label.setWordWrap(False)

        layout.addSpacing(4)
        layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.artist_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # ---------- Volume ----------
        volume_row = QHBoxLayout()
        volume_icon = QLabel()
        volume_icon.setPixmap(svg_to_icon(VOLUME_SVG, QSize(16, 16)).pixmap(16, 16))
        volume_icon.setStyleSheet("background: transparent;")

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setStyleSheet(SLIDER_STYLE)
        self.volume_slider.valueChanged.connect(self.volume_changed.emit)

        volume_row.addWidget(volume_icon)
        volume_row.addWidget(self.volume_slider)
        layout.addLayout(volume_row)

        # ---------- Wiring ----------
        self.play_btn.clicked.connect(self.play_pause_clicked.emit)
        self.next_btn.clicked.connect(self.next_clicked.emit)
        self.prev_btn.clicked.connect(self.prev_clicked.emit)

    # ---------- Public API ----------
    def set_playing(self, playing: bool):
        self.play_btn.setIcon(self._icon_pause if playing else self._icon_play)

    def set_track(self, title: str, artist: str):
        self._raw_title = title or self._raw_title
        self._raw_artist = artist or self._raw_artist
        self.refresh_labels()

    def set_volume(self, value: int):
        """Sync the slider from the controller without re-emitting volume_changed."""
        if self.volume_slider.isSliderDown():
            return
        self.volume_slider.blockSignals(True)
        self.volume_slider.setValue(value)
        self.volume_slider.blockSignals(False)

    def refresh_labels(self):
        if self._raw_title:
            metrics = QFontMetrics(self.title_label.font())
            width = max(self.title_label.width(), 200)
            elided = metrics.elidedText(self._raw_title, Qt.TextElideMode.ElideRight, width)
            self.title_label.setText(elided)

        if self._raw_artist:
            metrics = QFontMetrics(self.artist_label.font())
            width = max(self.artist_label.width(), 200)
            elided = metrics.elidedText(self._raw_artist, Qt.TextElideMode.ElideRight, width)
            self.artist_label.setText(elided)
