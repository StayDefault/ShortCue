# ShortCue
 ShortCue is a privacy-first Windows desktop coach that observes supported GUI operations, identifies verified keyboard shortcuts that could replace repeated pointer-driven actions, and teaches those shortcuts through unobtrusive contextual reminders.

## Development status

The prototype starts manually in the Windows system tray. It provides
a Pause/Resume control and an Exit action.

Pause/Resume currently updates the menu and tooltip only. GUI observation
and keyboard monitoring are not implemented yet.

## Run from source

Development environment: Windows 11, Python 3.14.6.

Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start ShortCue from the repository root:

```powershell
.\.venv\Scripts\python.exe -m shortcue
```

Right-click the tray icon to access its controls. The icon may appear
inside Windows' hidden-icons menu.

## Privacy

The current prototype does not observe application activity, capture
keyboard input, or persist learning data.