from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QFrame
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFontMetrics

from hoverx.ui.icons import svg_to_icon
from hoverx.ui.marquee_label import MarqueeLabel
from hoverx.ui.svg_icons import (
    PLAY_SVG, PAUSE_SVG, PLAY_SVG_DARK, PAUSE_SVG_DARK, NEXT_SVG, PREV_SVG, VOLUME_SVG,
)

# The play/pause button carries the primary action, so it gets its own
# light, filled, circular style; prev/next stay flat and secondary.
PLAY_BUTTON_STYLE = (
    "QPushButton { background: rgba(255,255,255,0.92); border-radius: 24px; }"
    "QPushButton:hover { background: rgba(255,255,255,1.0); }"
)
SECONDARY_BUTTON_STYLE = (
    "QPushButton { background: transparent; border-radius: 20px; }"
    "QPushButton:hover { background: rgba(255,255,255,0.12); }"
)

SLIDER_STYLE = """
QSlider::groove:vertical {
    background: rgba(255,255,255,0.15);
    width: 4px;
    border-radius: 2px;
}
QSlider::sub-page:vertical {
    background: rgba(255,255,255,0.6);
    border-radius: 2px;
}
QSlider::add-page:vertical {
    background: rgba(255,255,255,0.15);
    border-radius: 2px;
}
QSlider::handle:vertical {
    background: white;
    height: 12px;
    margin: 0 -4px;
    border-radius: 6px;
}
"""


class ControlsPanel(QWidget):
    """The expanded content area: transport buttons, track labels, volume slider."""

    play_pause_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    volume_changed = pyqtSignal(int)

    VOLUME_STEP = 5

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

        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 12, 12, 12)
        outer.setSpacing(10)

        layout = QVBoxLayout()
        layout.setSpacing(2)
        outer.addLayout(layout, 1)

        # ---------- Transport controls ----------
        controls = QHBoxLayout()
        controls.setSpacing(10)
        controls.addStretch()

        self.prev_btn = QPushButton()
        self.play_btn = QPushButton()
        self.next_btn = QPushButton()

        self._icon_play = svg_to_icon(PLAY_SVG_DARK, QSize(20, 20))
        self._icon_pause = svg_to_icon(PAUSE_SVG_DARK, QSize(20, 20))
        self.play_btn.setIcon(self._icon_play)
        self.play_btn.setIconSize(QSize(20, 20))
        self.play_btn.setFixedSize(48, 48)
        self.play_btn.setStyleSheet(PLAY_BUTTON_STYLE)

        self.prev_btn.setIcon(svg_to_icon(PREV_SVG, QSize(18, 18)))
        self.next_btn.setIcon(svg_to_icon(NEXT_SVG, QSize(18, 18)))
        for btn in (self.prev_btn, self.next_btn):
            btn.setIconSize(QSize(18, 18))
            btn.setFixedSize(40, 40)
            btn.setStyleSheet(SECONDARY_BUTTON_STYLE)

        controls.addWidget(self.prev_btn)
        controls.addWidget(self.play_btn)
        controls.addWidget(self.next_btn)
        controls.addStretch()
        layout.addLayout(controls)

        # ---------- Labels ----------
        layout.addSpacing(12)

        self.title_label = MarqueeLabel()
        self.title_label.setStyleSheet(
            "QLabel { background: transparent; border: none; color: white;"
            " font-size: 14px; font-weight: 600; }"
        )
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(False)

        self.artist_label = MarqueeLabel()
        self.artist_label.setStyleSheet(
            "QLabel { background: transparent; border: none; color: #9A9A9A; font-size: 12px; }"
        )
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.artist_label.setWordWrap(False)

        layout.addWidget(self.title_label)
        layout.addWidget(self.artist_label)
        layout.addStretch(1)

        # ---------- Divider ----------
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setStyleSheet("background: rgba(255,255,255,0.10); border: none; max-width: 1px; min-width: 1px;")
        outer.addWidget(divider)

        # ---------- Volume (vertical, side column) ----------
        volume_col = QVBoxLayout()
        volume_col.setSpacing(6)

        self.volume_label = QLabel("0%")
        self.volume_label.setStyleSheet(
            "QLabel { background: transparent; border: none; color: #CFCFCF; font-size: 11px; }"
        )
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Fixed width sized to the widest possible value ("100%") - otherwise
        # the label's natural width shrinks/grows as the digit count changes
        # (e.g. "5%" vs "100%"), which reflows this whole QHBoxLayout and
        # visibly shifts the divider every time the volume changes.
        widest = QFontMetrics(self.volume_label.font()).horizontalAdvance("100%")
        self.volume_label.setFixedWidth(widest + 4)

        self.volume_slider = QSlider(Qt.Orientation.Vertical)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setSingleStep(self.VOLUME_STEP)
        self.volume_slider.setPageStep(self.VOLUME_STEP * 2)
        self.volume_slider.setFixedWidth(20)
        self.volume_slider.setStyleSheet(SLIDER_STYLE)
        self.volume_slider.valueChanged.connect(self._on_slider_value_changed)

        volume_icon = QLabel()
        volume_icon.setPixmap(svg_to_icon(VOLUME_SVG, QSize(16, 16)).pixmap(16, 16))
        volume_icon.setStyleSheet("background: transparent;")

        volume_col.addWidget(self.volume_label, 0, alignment=Qt.AlignmentFlag.AlignHCenter)
        volume_col.addWidget(self.volume_slider, 1, alignment=Qt.AlignmentFlag.AlignHCenter)
        volume_col.addWidget(volume_icon, 0, alignment=Qt.AlignmentFlag.AlignHCenter)
        outer.addLayout(volume_col)

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
        self.volume_label.setText(f"{value}%")

    def refresh_labels(self):
        if self._raw_title:
            self.title_label.setMarqueeText(self._raw_title)
        if self._raw_artist:
            self.artist_label.setMarqueeText(self._raw_artist)

    def hideEvent(self, event):
        # Don't burn CPU scrolling marquees while the panel is collapsed/hidden.
        self.title_label.pause()
        self.artist_label.pause()
        super().hideEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.title_label.resume()
        self.artist_label.resume()

    # ---------- Volume interaction ----------
    def _on_slider_value_changed(self, value: int):
        self.volume_label.setText(f"{value}%")
        self.volume_changed.emit(value)

    def wheelEvent(self, event):
        """Let scrolling anywhere over the expanded panel adjust volume, not
        just the ~20px-wide slider strip itself."""
        delta = event.angleDelta().y()
        if delta == 0:
            return
        step = self.VOLUME_STEP if delta > 0 else -self.VOLUME_STEP
        new_value = max(0, min(100, self.volume_slider.value() + step))
        self.volume_slider.setValue(new_value)
        event.accept()
