import sys,os,subprocess
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from hoverx.ui.widget import FloatingWidget
from hoverx.controller.dummy import DummyController
from hoverx.version import __version__
from hoverx.updater.checker import check_for_update
from hoverx.updater.downloader import download_update

try:
    from hoverx.controller.windows_smtc import WindowsSMTCController
    controller = WindowsSMTCController()
except Exception as e:
    controller = DummyController()

def main():
    update_info = check_for_update()

    if update_info:
        try:
            new_path = download_update(update_info["url"])
            trigger_update(new_path)
            return
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("HoverX")
    app.setOrganizationName("HoverX")

    try:
        from hoverx.controller.windows_smtc import WindowsSMTCController
        controller = WindowsSMTCController()
    except Exception:
        controller = DummyController()

    widget = FloatingWidget(controller)
    widget.show()

    tray = QSystemTrayIcon()
    tray.setParent(app)
    tray.setIcon(QIcon(resource_path("assets/icons/icon.ico")))
    tray.setToolTip("HoverX")

    menu = QMenu()
    menu.addAction("Show HoverX", widget.show)
    menu.addAction("Hide HoverX", widget.hide)
    menu.addSeparator()
    menu.addAction("Exit HoverX", app.quit)

    tray.setContextMenu(menu)
    tray.show()

    app.setQuitOnLastWindowClosed(False)
    sys.exit(app.exec())


def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, relative_path)
    return relative_path

def trigger_update(new_exe_path):
    current_exe = sys.executable

    updater = r"E:\Projects\HoverX\dist"  # TEMP, hardcoded for now

    subprocess.Popen([
        updater,
        current_exe,
        new_exe_path
    ])

    sys.exit(0)

if __name__ == "__main__":
    main()