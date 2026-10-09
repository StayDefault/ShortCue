"""Connect the tray lifecycle to local database initialization."""

import sys

from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from shortcue.monitoring import MonitoringState
from shortcue.paths import database_path
from shortcue.storage import StorageError, initialize_database
from shortcue.tray import TrayController


def main() -> int:
    """Start the Windows tray application and return its exit code."""
    if sys.platform != "win32":
        print("ShortCue requires Windows 11.", file=sys.stderr)
        return 1

    app = QApplication(sys.argv)
    app.setApplicationName("ShortCue")
    # Closing future search/settings windows must not end tray operation.
    app.setQuitOnLastWindowClosed(False)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("ShortCue could not access the system tray.", file=sys.stderr)
        return 1

    try:
        initialize_database(database_path())
    except (StorageError, RuntimeError):
        # Fixed text avoids exposing database contents or private paths in logs.
        print("ShortCue could not initialize local storage.", file=sys.stderr)
        QMessageBox.critical(
            None,
            "ShortCue — startup failed",
            "Local storage could not be initialized. Check folder permissions "
            "and database compatibility. No database was reset. ShortCue will exit.",
        )
        return 1

    # Pause is session-only; database contents never select the starting state.
    tray = TrayController(app, MonitoringState())
    app.aboutToQuit.connect(tray.hide)
    tray.show()
    return app.exec()
