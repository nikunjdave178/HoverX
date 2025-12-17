import sys,os
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from hoverx.ui.widget import FloatingWidget
from hoverx.controller.dummy import DummyController

try:
    from hoverx.controller.windows_smtc import WindowsSMTCController
    controller = WindowsSMTCController()
except Exception as e:
    controller = DummyController()

def main():
    app = QApplication(sys.argv)

    app.setApplicationName("HoverX")
    app.setOrganizationName("HoverX")

    widget = FloatingWidget(controller)
    widget.show()

    # ----- System Tray -----
    tray = QSystemTrayIcon(widget)
    icon = QIcon(resource_path("assets/icons/icon.ico"))
    tray.setIcon(icon)  # MUST NOT be empty
    tray.setToolTip("HoverX")

    menu = QMenu()

    show_action = menu.addAction("Show HoverX")
    hide_action = menu.addAction("Hide HoverX")
    menu.addSeparator()
    exit_action = menu.addAction("Exit HoverX")

    show_action.triggered.connect(widget.show)
    hide_action.triggered.connect(widget.hide)
    exit_action.triggered.connect(app.quit)

    tray.setContextMenu(menu)
    tray.show()

    app.setQuitOnLastWindowClosed(False)

    sys.exit(app.exec())

def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, relative_path)
    return relative_path

if __name__ == "__main__":
    main()