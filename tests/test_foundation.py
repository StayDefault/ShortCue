"""Behavior checks using temporary databases and Qt's offscreen platform."""

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import io
import sqlite3
import unittest
from contextlib import closing, redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from shortcue import application
from shortcue.monitoring import MonitoringState
from shortcue.paths import database_path
from shortcue.storage import SCHEMA_VERSION, StorageError, initialize_database
from shortcue.tray import TrayController


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "nested" / "shortcue.sqlite3"

    def test_initialization_is_repeatable_and_creates_no_pause_table(self):
        initialize_database(self.path)
        initialize_database(self.path)
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute(
                "SELECT version FROM schema_metadata"
            ).fetchall(), [(SCHEMA_VERSION,)])
            self.assertEqual(connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall(), [("schema_metadata",)])
        # Windows refuses this rename if initialization left an open handle.
        self.path.rename(self.path.with_suffix(".backup"))

    def test_legacy_pause_data_is_preserved_but_not_adopted(self):
        self.path.parent.mkdir()
        with closing(sqlite3.connect(self.path)) as connection:
            with connection:
                connection.execute("CREATE TABLE monitoring_settings (id, paused)")
                connection.execute("INSERT INTO monitoring_settings VALUES (1, 1)")
        initialize_database(self.path)
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute(
                "SELECT paused FROM monitoring_settings"
            ).fetchone(), (1,))
        self.assertFalse(MonitoringState().paused)

    def test_future_schema_is_rejected_without_overwriting_it(self):
        initialize_database(self.path)
        with closing(sqlite3.connect(self.path)) as connection:
            with connection:
                connection.execute("UPDATE schema_metadata SET version = 999")
        with self.assertRaises(StorageError):
            initialize_database(self.path)
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute(
                "SELECT version FROM schema_metadata"
            ).fetchone(), (999,))

    def test_invalid_database_is_not_reset(self):
        self.path.parent.mkdir()
        original = b"not a SQLite database"
        self.path.write_bytes(original)
        with self.assertRaises(StorageError):
            initialize_database(self.path)
        self.assertEqual(self.path.read_bytes(), original)

    def test_unusable_parent_reports_storage_error(self):
        self.path.parent.write_text("This is a file, not a directory.")
        with self.assertRaises(StorageError):
            initialize_database(self.path)

    def test_locked_database_reports_storage_error(self):
        initialize_database(self.path)
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            with self.assertRaises(StorageError):
                initialize_database(self.path)
            connection.rollback()
        initialize_database(self.path)


class QtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setApplicationName("ShortCue")

    def test_menu_clicks_update_shared_state_and_presentation(self):
        state = MonitoringState()
        tray = TrayController(self.app, state)
        self.assertFalse(tray.pause_action.isChecked())
        self.assertFalse(tray.tray.icon().isNull())
        tray.pause_action.trigger()
        self.assertTrue(state.paused)
        self.assertEqual(tray.pause_action.text(), "Resume monitoring")
        self.assertIn("monitoring paused", tray.tray.toolTip())
        tray.pause_action.trigger()
        self.assertFalse(state.paused)
        self.assertEqual(tray.pause_action.text(), "Pause monitoring")
        self.assertIn("observer not connected", tray.tray.toolTip())

    def test_new_controller_always_starts_enabled(self):
        first = TrayController(self.app, MonitoringState())
        first.pause_action.trigger()
        second = TrayController(self.app, MonitoringState())
        self.assertFalse(second.monitoring.paused)
        self.assertFalse(second.pause_action.isChecked())
        self.assertIn("monitoring enabled", second.tray.toolTip())

    def test_programmatic_pause_updates_checkmark(self):
        tray = TrayController(self.app, MonitoringState())
        tray.set_paused(True)
        self.assertTrue(tray.pause_action.isChecked())

    def test_exit_action_requests_quit(self):
        with patch.object(self.app, "quit") as quit_app:
            tray = TrayController(self.app, MonitoringState())
            tray.exit_action.trigger()
            quit_app.assert_called_once()

    def test_path_is_absolute_and_does_not_create_database(self):
        with TemporaryDirectory() as folder:
            target = Path(folder) / "not-created"
            with patch("shortcue.paths.QStandardPaths.writableLocation",
                       return_value=str(target)):
                self.assertEqual(database_path(), target / "shortcue.sqlite3")
                self.assertFalse(target.exists())

    def test_missing_path_fails_explicitly(self):
        with patch("shortcue.paths.QStandardPaths.writableLocation", return_value=""):
            with self.assertRaises(RuntimeError):
                database_path()

    def test_startup_storage_failure_exits_before_creating_tray(self):
        with patch.object(application.sys, "platform", "win32"), \
             patch.object(application, "QApplication", return_value=self.app), \
             patch.object(application.QSystemTrayIcon, "isSystemTrayAvailable", return_value=True), \
             patch.object(application, "initialize_database", side_effect=StorageError("private data")), \
             patch.object(application.QMessageBox, "critical") as message, \
             patch.object(application, "TrayController") as controller, \
             redirect_stderr(io.StringIO()) as output:
            self.assertEqual(application.main(), 1)
            message.assert_called_once()
            controller.assert_not_called()
            self.assertNotIn("private data", output.getvalue())

    def test_missing_tray_does_not_initialize_storage(self):
        with patch.object(application.sys, "platform", "win32"), \
             patch.object(application, "QApplication", return_value=self.app), \
             patch.object(application.QSystemTrayIcon, "isSystemTrayAvailable", return_value=False), \
             patch.object(application, "initialize_database") as storage, \
             redirect_stderr(io.StringIO()):
            self.assertEqual(application.main(), 1)
            storage.assert_not_called()

    def test_startup_event_loop_and_exit_with_real_temporary_storage(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "shortcue.sqlite3"
            controllers = []

            def create_controller(app, state):
                controller = TrayController(app, state)
                controllers.append(controller)
                # Exercise the real event loop without showing native tray UI.
                controller.show = lambda: QTimer.singleShot(
                    0, controller.exit_action.trigger
                )
                return controller

            with patch.object(application.sys, "platform", "win32"), \
                 patch.object(application, "QApplication", return_value=self.app), \
                 patch.object(application.QSystemTrayIcon, "isSystemTrayAvailable", return_value=True), \
                 patch.object(application, "database_path", return_value=path), \
                 patch.object(application, "TrayController", side_effect=create_controller):
                self.assertEqual(application.main(), 0)
            self.assertTrue(path.exists())
            self.assertFalse(controllers[0].monitoring.paused)
            self.assertFalse(controllers[0].tray.isVisible())


if __name__ == "__main__":
    unittest.main()
