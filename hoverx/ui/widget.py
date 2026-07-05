import time
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect, QPropertyAnimation, QTimer
from PyQt6.QtGui import QPainter, QColor, QCursor

from hoverx.ui.controls_panel import ControlsPanel

# How often the hover-safety-net timer re-checks the real cursor position.
# See FloatingWidget._check_hover for why this exists.
HOVER_POLL_MS = 120


class FloatingWidget(QWidget):
    ICON_SIZE = 56
    EXPANDED_WIDTH = 320
    EXPANDED_HEIGHT = 150

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        self._manual_toggle_ts = 0.0
        self._expanded = False
        self._dragging = False
        self._drag_offset = None

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
        self._anim.finished.connect(self._on_anim_finished)

        # Expanded content panel
        self.controls_panel = ControlsPanel(self)
        self.controls_panel.setGeometry(0, 0, self.EXPANDED_WIDTH, self.EXPANDED_HEIGHT)
        self.controls_panel.hide()
        self.controls_panel.installEventFilter(self)

        self.controls_panel.set_playing(self.controller.is_playing())
        self.controls_panel.play_pause_clicked.connect(self._on_play_clicked)
        self.controls_panel.next_clicked.connect(self.controller.next)
        self.controls_panel.prev_clicked.connect(self.controller.previous)
        self.controls_panel.volume_changed.connect(self._on_volume_changed)

        # ---------- Track info update ----------
        self.track_timer = QTimer(self)
        self.track_timer.setInterval(1000)
        self.track_timer.timeout.connect(self.update_track_info)
        self.track_timer.start()

        # ---------- Hover safety net ----------
        # enterEvent/leaveEvent alone are not reliable: Windows delivers
        # leaveEvent via WM_MOUSELEAVE, which requires TrackMouseEvent to
        # have been armed by a prior mouse-move inside the window. If the
        # cursor crosses this widget fast enough, that arming can be skipped
        # entirely, so leaveEvent never fires and the widget is stuck
        # expanded. This timer polls the real cursor position as a
        # self-healing fallback regardless of any single missed native event.
        self._hover_poll = QTimer(self)
        self._hover_poll.setInterval(HOVER_POLL_MS)
        self._hover_poll.timeout.connect(self._check_hover)
        self._hover_poll.start()

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
        self.expand()

    def leaveEvent(self, event):
        if not self.rect().contains(self.mapFromGlobal(QCursor.pos())):
            self.collapse()

    def _check_hover(self):
        """Safety-net fallback for missed native leave events (see __init__)."""
        if not self._expanded or self._dragging:
            return
        if not self.frameGeometry().contains(QCursor.pos()):
            self.collapse()

    # ---------- Expand / Collapse ----------
    def expand(self):
        if self._expanded:
            return
        self._expanded = True
        self.controls_panel.show()
        self._animate_to(
            QRect(self.x(), self.y(), self.EXPANDED_WIDTH, self.EXPANDED_HEIGHT)
        )
        QTimer.singleShot(0, self._refresh_content)

    def collapse(self):
        if not self._expanded:
            return
        self._expanded = False
        self._animate_to(
            QRect(self.x(), self.y(), self.ICON_SIZE, self.ICON_SIZE)
        )

    def _animate_to(self, rect):
        self._anim.stop()
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(rect)
        self._anim.start()

    def _on_anim_finished(self):
        # Reflects self._expanded at actual completion time, not whatever it
        # was when the (possibly superseded) animation was started - this is
        # what stays correct if expand()/collapse() re-trigger mid-animation.
        if not self._expanded:
            self.controls_panel.hide()
            self.update()

    # ---------- Keep content synced ----------
    def resizeEvent(self, event):
        self.controls_panel.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)
        self.controls_panel.refresh_labels()

    def update_track_info(self):
        now = time.perf_counter()

        # debounce after manual click
        if now - self._manual_toggle_ts < 0.4:
            return

        title, artist = self.controller.get_track_info()
        self.controls_panel.set_playing(self.controller.is_playing())
        self.controls_panel.set_track(title, artist)
        self.controls_panel.set_volume(self.controller.get_volume())

    def _refresh_content(self):
        """Force an immediate refresh right after expand(), instead of waiting
        for the next track_timer tick, so hovering never shows stale data."""
        self.controls_panel.refresh_labels()
        self.controls_panel.set_volume(self.controller.get_volume())

    # ---------- Dragging ----------
    def eventFilter(self, obj, event):
        if obj is self.controls_panel:
            if event.type() == event.Type.MouseButtonPress:
                if event.buttons() & Qt.MouseButton.LeftButton:
                    # prevent dragging when clicking buttons/slider
                    if self.controls_panel.childAt(event.position().toPoint()):
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

        # optimistic flip ONLY
        self.controls_panel.set_playing(not self.controller.is_playing())

        self.controller.play_pause()

    def _on_volume_changed(self, value: int):
        self.controller.set_volume(value)
