# ShortCue

ShortCue is a privacy-first Windows desktop coach being developed to teach
verified keyboard shortcuts for repeated, supported GUI actions.

## Current foundation

The current version starts manually in the Windows system tray, provides
Pause/Resume and Exit, and initializes a local SQLite database. Every launch
starts enabled. Pause only applies to the current session.

The observer is not connected: enabled means the user allows future monitoring,
not that any activity is currently observed. The tooltip says this explicitly.
Search, assistant, settings, exclusions, reminders, keyboard hooks, shortcut
manifests, and learning data are not implemented. Ollama is not needed yet.

## Run from source

Development platform: Windows 11, Python 3.14.6, PySide6 6.11.2.
Run these commands from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m shortcue
```

Right-click the icon near the Windows clock (possibly inside the hidden-icons
menu). Pausing changes the icon, checkmark, menu label, and tooltip. Exit removes
the icon and ends the process. Closing future application windows will not exit
the tray process. Multiple launches currently create separate instances; run
only one instance while testing.

If the virtual-environment launcher fails, first check that the Python
installation referenced by `.venv/pyvenv.cfg` still exists. A recreated virtual
environment needs dependencies installed again.

## Storage and privacy

Qt resolves the database to the current user's local application-data folder,
normally `%LOCALAPPDATA%\ShortCue\shortcue.sqlite3`. It is outside the repository.
Startup creates missing directories and initializes `schema_metadata`, a
single-row table holding schema version 1. Future data tables and migrations
will be introduced with their own milestones.

Pause is never written to or restored from SQLite. If the earlier learning
example created `monitoring_settings`, that table is left intact but ignored.
No existing database or user data is automatically deleted or reset.

Invalid, locked, inaccessible, or unsupported-version databases cause a clear
startup error and exit. A failed initialization can leave a newly created file
or directory; it does not reset an existing database. Connections are closed
before the GUI event loop starts.

This version observes no GUI activity or keyboard input, collects no typed
text, clipboard contents, screenshots, or terminal commands, and makes no
network requests. There is no diagnostic file logging. Startup errors use fixed
messages rather than dumping database contents or private paths.

## Automated checks

The standard-library test runner needs no additional dependency:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests use temporary databases and Qt's offscreen platform. They cover schema
initialization, repeated startup, legacy-data preservation, database failures,
menu/state synchronization, fresh-session defaults, startup failure handling,
and the event loop's Exit path. They do not verify Windows tray placement or
native tooltip appearance.

## Manual Windows verification

1. Start one instance. Confirm an icon appears without an application window.
2. Hover: confirm `monitoring enabled (observer not connected)`.
3. Click Pause monitoring. Confirm the pause icon, checked Resume monitoring
   action, and paused tooltip.
4. Resume. Confirm the enabled icon, unchecked Pause monitoring, and tooltip.
5. Pause again, Exit, and restart. Confirm it starts enabled.
6. Exit. Confirm the icon disappears and the terminal prompt returns.
7. Run without Ollama: the same controls should work.

See `docs/foundation.md` for the code walkthrough and verification record.

## License and references

ShortCue's source is MIT licensed; dependencies retain their own licenses.
PySide6/Qt licensing and distribution obligations must be reviewed before a
packaged release. No external example source or shortcut dataset was copied.

Independent references:

- [Qt's complete Python tray example](https://doc.qt.io/qtforpython-6/examples/example_widgets_desktop_systray.html)
- [Python SQLite tutorial and transaction documentation](https://docs.python.org/3.14/library/sqlite3.html)
- [Qt standard application-data paths](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QStandardPaths.html)
