import os

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon


def build_tray_icon(app, widget, icon_path: str) -> QSystemTrayIcon:
    tray = QSystemTrayIcon()
    tray.setParent(app)
    tray.setIcon(QIcon(icon_path))
    tray.setToolTip("HoverX")

    menu = QMenu()
    menu.addAction("Show HoverX", widget.show)
    menu.addAction("Hide HoverX", widget.hide)
    menu.addSeparator()
    menu.addAction("Exit HoverX", lambda: os._exit(0))

    tray.setContextMenu(menu)
    tray.show()
    return tray
