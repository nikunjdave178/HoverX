import sys
import os
import subprocess
import traceback

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon
from PyQt6.QtCore import QTimer

from hoverx.ui.widget import FloatingWidget
from hoverx.controller.dummy import DummyController
from hoverx.tray.tray_icon import build_tray_icon
from hoverx.updater.checker import check_for_update
from hoverx.updater.downloader import download_update
from hoverx.logging_utils import log


# --------------------------------------------------
# Utils
# --------------------------------------------------

def app_dir():
    """Directory where HoverX.exe lives"""
    return os.path.dirname(sys.executable)


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


def check_and_update(tray: QSystemTrayIcon):
    try:
        update_info = check_for_update()
        if not update_info:
            return

        remote_version = update_info.get("version", "?")
        log(f"Update available: {remote_version}")
        tray.showMessage(
            "HoverX update available",
            f"Downloading version {remote_version}...",
            QSystemTrayIcon.MessageIcon.Information,
        )

        new_path = download_update(update_info["url"])

        tray.showMessage(
            "HoverX",
            "Update downloaded - restarting to finish updating.",
            QSystemTrayIcon.MessageIcon.Information,
        )
        trigger_update(new_path)

    except Exception as e:
        log("Update failed:")
        log(traceback.format_exc())
        tray.showMessage(
            "HoverX update failed",
            str(e),
            QSystemTrayIcon.MessageIcon.Warning,
        )


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

    app.aboutToQuit.connect(controller.shutdown)

    widget = FloatingWidget(controller)
    widget.show()

    tray = build_tray_icon(app, widget, resource_path("assets/icons/icon.ico"))

    app.setQuitOnLastWindowClosed(False)

    # Cleanup backup only after UI is live
    cleanup_backup()

    # Run update check AFTER Qt is stable
    QTimer.singleShot(0, lambda: check_and_update(tray))

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
