from pathlib import Path

from PySide6.QtCore import QStandardPaths


def database_path() -> Path:
    """Return the local database path without creating files."""
    location = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppLocalDataLocation
    )
    if not location:
        raise RuntimeError("Local application-data location is unavailable.")

    return Path(location) / "shortcue.sqlite3"