from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtSvg import QSvgRenderer


def svg_to_icon(svg_xml: str, size: QSize) -> QIcon:
    renderer = QSvgRenderer(bytearray(svg_xml, encoding="utf-8"))
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)
