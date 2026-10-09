"""Tray presentation for the current session's monitoring state."""

from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon

from shortcue.monitoring import MonitoringState


class TrayController(QObject):
    """Own the tray objects and translate menu clicks into session state."""

    def __init__(self, app: QApplication, monitoring: MonitoringState) -> None:
        super().__init__(app)
        self.monitoring = monitoring
        self.tray = QSystemTrayIcon(self)
        self.menu = QMenu()
        self.pause_action = self.menu.addAction("Pause monitoring")
        self.pause_action.setCheckable(True)
        # Initialize before connecting so setup does not simulate a user click.
        self.pause_action.setChecked(monitoring.paused)
        self.pause_action.toggled.connect(self.set_paused)
        self.menu.addSeparator()
        self.exit_action = self.menu.addAction("Exit")
        self.exit_action.triggered.connect(app.quit)
        self.tray.setContextMenu(self.menu)
        self._refresh()

    @Slot(bool)
    def set_paused(self, paused: bool) -> None:
        """Apply the user's session state without touching persistence."""
        self.monitoring.paused = paused
        self._refresh()

    def _refresh(self) -> None:
        """Keep the checkmark, action text, icon, and tooltip consistent."""
        paused = self.monitoring.paused
        # Programmatic refresh must not trigger another state change.
        previous = self.pause_action.blockSignals(True)
        try:
            self.pause_action.setChecked(paused)
        finally:
            self.pause_action.blockSignals(previous)
        self.pause_action.setText("Resume monitoring" if paused else "Pause monitoring")
        state = "paused" if paused else "enabled"
        self.tray.setToolTip(
            f"ShortCue — monitoring {state} (observer not connected)"
        )
        icon_type = (
            QStyle.StandardPixmap.SP_MediaPause
            if paused else QStyle.StandardPixmap.SP_ComputerIcon
        )
        self.tray.setIcon(QApplication.style().standardIcon(icon_type))

    @Slot()
    def show(self) -> None:
        """Show the tray icon without opening an application window."""
        self.tray.show()

    @Slot()
    def hide(self) -> None:
        """Remove the tray icon during shutdown."""
        self.tray.hide()
