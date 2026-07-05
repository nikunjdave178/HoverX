from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFontMetrics, QPainter


class MarqueeLabel(QLabel):
    """A QLabel that scrolls its text left in a seamless loop when it's too
    wide to fit, instead of eliding it with "...". Renders as a normal
    (e.g. centered) QLabel whenever the text does fit."""

    GAP_PX = 40
    TICK_MS = 40
    STEP_PX = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._full_text = ""
        self._offset = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(self.TICK_MS)
        self._timer.timeout.connect(self._advance)

    def setMarqueeText(self, text: str):
        if text == self._full_text:
            # Same text as already displayed (e.g. the 1s track-info poll
            # re-reporting an unchanged title) - leave any in-progress scroll
            # alone. Resetting here was the bug: it snapped the offset back
            # to 0 every ~1s, which looked like the marquee restarting from
            # the beginning instead of looping seamlessly.
            return
        self._full_text = text
        self._offset = 0.0
        super().setText(text)
        self._sync_marquee_state()

    def pause(self):
        self._timer.stop()

    def resume(self):
        self._sync_marquee_state()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_marquee_state()

    def hideEvent(self, event):
        self.pause()
        super().hideEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.resume()

    def paintEvent(self, event):
        if not self._timer.isActive():
            super().paintEvent(event)
            return

        metrics = QFontMetrics(self.font())
        text_w = metrics.horizontalAdvance(self._full_text)
        y = (self.height() - metrics.height()) // 2 + metrics.ascent()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setClipRect(self.rect())
        painter.setFont(self.font())
        painter.setPen(self.palette().color(self.foregroundRole()))

        x = -int(self._offset)
        while x < self.width():
            painter.drawText(x, y, self._full_text)
            x += text_w + self.GAP_PX

    def _text_width(self) -> int:
        return QFontMetrics(self.font()).horizontalAdvance(self._full_text)

    def _sync_marquee_state(self):
        overflow = self._full_text and self._text_width() > self.width()
        if overflow and not self._timer.isActive():
            self._offset = 0.0
            self._timer.start()
        elif not overflow and self._timer.isActive():
            self._timer.stop()
            self._offset = 0.0
        self.update()

    def _advance(self):
        text_w = self._text_width()
        if text_w <= 0:
            return
        loop_len = text_w + self.GAP_PX
        self._offset = (self._offset + self.STEP_PX) % loop_len
        self.update()
