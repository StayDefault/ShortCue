import sys

from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QStyle,
    QSystemTrayIcon,
)


def main() -> int:
    """Run the tray application and return its exit code."""
    
    app = QApplication(sys.argv)
    app.setApplicationName("ShortCue")
    
    # Keep the tray process running when no application windows are open.
    app.setQuitOnLastWindowClosed(False)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("System tray is unavailable.", file=sys.stderr)
        return 1

    icon = app.style().standardIcon(
        QStyle.StandardPixmap.SP_ComputerIcon
    )

    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("ShortCue — development version")

    menu = QMenu()
    
    # Checked means paused; the observer will use this state later.
    pause_action = menu.addAction("Pause monitoring")
    pause_action.setCheckable(True)

    def update_monitoring_state(paused: bool) -> None:
        """Update the menu and tooltip to reflect the pause state."""
        
        pause_action.setText(
            "Resume monitoring" if paused else "Pause monitoring"
        )
        state = "paused" if paused else "enabled"
        tray.setToolTip(
            f"ShortCue — monitoring {state} (observer not connected)"
        )

    pause_action.toggled.connect(update_monitoring_state)
    update_monitoring_state(False)

    menu.addSeparator()
    
    exit_action = menu.addAction("Exit")
    exit_action.triggered.connect(app.quit)

    tray.setContextMenu(menu)
    tray.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())