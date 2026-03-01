# SilverMill Desktop Launcher

Run SilverMill as a desktop application so the admin does **not** need to run `python app.py` every time. One start and the system runs with load balancing.

## Put SilverMill on the Desktop (recommended)

1. **First-time setup** (once):
   - Install dependencies: `pip install -r requirements.txt`
   - Double-click **`Create Desktop Shortcut.bat`**
   - This creates **SilverMill.ico** (app icon) and a **SilverMill** shortcut on your Desktop.

2. **Start SilverMill** (every time):
   - Double-click **SilverMill** on your **Desktop** (or double-click **`Start SilverMill.bat`** in the project folder).

   The app will:
   - Start the server with **16 worker threads** (load balancing)
   - Open your default browser at http://127.0.0.1:8080
   - Keep running until you press **Ctrl+C** in the server window (or close it).

Admin can start the system directly from the Desktop; no need to open the project folder or run `python app.py`.

## Quick start (without desktop shortcut)

1. **First-time setup** (once): `pip install -r requirements.txt`
2. **Start:** Double-click **`Start SilverMill.bat`** in the SilverMill folder, or run `python launcher.py` from a terminal.

## How the icon and desktop shortcut work

| What | How it works |
|------|----------------|
| **Icon** | Running **Create Desktop Shortcut.bat** runs **create_icon.py**, which creates **SilverMill.ico** in the project folder. If you have Pillow and `static/images/logo.png`, the icon is generated from your logo; otherwise a simple purple fallback icon is created (no extra install needed). |
| **Desktop shortcut** | **Create-DesktopShortcut.ps1** (PowerShell) creates a shortcut on your Windows Desktop named **SilverMill**. The shortcut runs **Start SilverMill.bat** with the project folder as working directory and uses **SilverMill.ico** as its icon. |
| **Changing the icon later** | Replace **SilverMill.ico** in the SilverMill folder with your own .ico file, then run **Create Desktop Shortcut.bat** again to refresh the shortcut. Or use a higher-quality logo at `static/images/logo.png` and install Pillow (`pip install Pillow`), then run **Create Desktop Shortcut.bat** again. |

## What the launcher does

| Feature | Description |
|--------|-------------|
| **Desktop-style start** | One double-click (or one command) starts everything. |
| **Load balancing** | Uses **Waitress** with 16 threads so many requests and camera feeds are handled without blocking. |
| **Auto-open browser** | Browser opens to the dashboard after ~2.5 seconds. |
| **Same app** | Same Flask app, same ports and features; only the way you start it changes. |

## Optional: build a single .exe (Windows)

If you want a **single .exe** that admins can run without installing Python:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build (from the `SilverMill` folder):
   ```bash
   pyinstaller --name SilverMill --onefile --console --add-data "templates;templates" --add-data "static;static" --hidden-import waitress launcher.py
   ```
   (Use `;` for Windows, `:` for Linux/Mac in `--add-data`.)

3. The executable will be in `dist/SilverMill.exe`. Copy the whole `SilverMill` folder (with `instance`, `train_models`, etc.) next to the exe or set the exe’s working directory to that folder so the app finds templates, static files, and the database.

**Note:** A one-file exe for this project can be large (hundreds of MB) because of OpenCV and other dependencies. For daily use, **`Start SilverMill.bat`** or **`python launcher.py`** is usually enough.

## Port and threads

- **Port:** 8080 (same as `app.py`). Change `PORT` in `launcher.py` if needed.
- **Threads:** 16 by default. Change `THREADS` in `launcher.py` to adjust load balancing (e.g. 8 or 32).

## Stopping the app

- In the launcher window (terminal): press **Ctrl+C**
- Or close the terminal window

Then start again anytime with **`Start SilverMill.bat`** or **`python launcher.py`**.
