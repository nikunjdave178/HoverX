import sys
import os
import subprocess
import traceback

from PyQt6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QMenu
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer

from hoverx.ui.widget import FloatingWidget
from hoverx.controller.dummy import DummyController
from hoverx.updater.checker import check_for_update
from hoverx.updater.downloader import download_update


# --------------------------------------------------
# Utils
# --------------------------------------------------

def app_dir():
    """Directory where HoverX.exe lives"""
    return os.path.dirname(sys.executable)


def log(msg):
    """Very simple updater-safe logging"""
    try:
        with open(os.path.join(os.getenv("TEMP"), "hoverx.log"), "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def cleanup_backup():
    """Delete .bak only after successful launch"""
    exe = sys.executable
    bak = exe + ".bak"

    if os.path.exists(bak):
        try:
            os.remove(bak)
            log("Backup cleaned")
        except Exception as e:
            log(f"Failed to clean backup: {e}")


# --------------------------------------------------
# Update logic
# --------------------------------------------------

def trigger_update(new_exe_path):
    current_exe = sys.executable
    updater = os.path.join(app_dir(), "HoverX_updater.exe")

    if not os.path.exists(updater):
        log("Updater EXE not found")
        return

    log("Triggering update")

    QApplication.quit()

    subprocess.Popen(
        [updater, current_exe, new_exe_path],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True
    )

    # Hard exit: required for Windows updater reliability
    os._exit(0)


def check_and_update():
    try:
        update_info = check_for_update()
        if not update_info:
            return

        log("Update available")

        new_path = download_update(update_info["url"])
        trigger_update(new_path)

    except Exception as e:
        log("Update failed:")
        log(traceback.format_exc())


# --------------------------------------------------
# Main app
# --------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("HoverX")
    app.setOrganizationName("HoverX")

    # Controller (single initialization)
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
    menu.addAction("Exit HoverX", lambda: os._exit(0))

    tray.setContextMenu(menu)
    tray.show()

    app.setQuitOnLastWindowClosed(False)

    # Cleanup backup only after UI is live
    cleanup_backup()

    # Run update check AFTER Qt is stable
    QTimer.singleShot(0, check_and_update)

    sys.exit(app.exec())


# --------------------------------------------------
# PyInstaller resource helper
# --------------------------------------------------

def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, relative_path)
    return relative_path


# --------------------------------------------------
# Entry
# --------------------------------------------------

if __name__ == "__main__":
    main()
