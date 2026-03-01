"""
SilverMill Desktop Launcher
----------------------------
Run this to start SilverMill as a desktop application:
- Uses Waitress (multi-threaded) for load balancing and stable serving
- Opens the default browser automatically so admin doesn't need to run python app.py
- No need to open a terminal or run commands again

Double-click: Start SilverMill.bat (Windows) or run: python launcher.py
"""
import os
import sys
import threading
import time
import webbrowser

# Ensure we run from the SilverMill project directory (where app.py, instance/, templates/, static/ live)
LAUNCHER_DIR = os.path.dirname(os.path.abspath(__file__))
if os.getcwd() != LAUNCHER_DIR:
    os.chdir(LAUNCHER_DIR)
if LAUNCHER_DIR not in sys.path:
    sys.path.insert(0, LAUNCHER_DIR)

HOST = "0.0.0.0"
PORT = 8080
URL = "http://127.0.0.1:%s" % PORT
THREADS = 16  # Load balancing: number of worker threads for handling requests


def open_browser():
    """Open default browser after a short delay so the server is ready."""
    time.sleep(2.5)
    try:
        webbrowser.open(URL)
    except Exception:
        print("Open your browser and go to: %s" % URL)


def main():
    print("SilverMill Desktop Launcher")
    print("Starting server with %d threads (load balancing)..." % THREADS)
    print("Browser will open at: %s" % URL)
    print("Press Ctrl+C to stop the server.\n")

    # Import app and run startup tasks (background threads, model preload)
    import app as app_module
    app_module.run_startup_tasks()

    # Serve with Waitress (multi-threaded, production-style on Windows)
    try:
        import waitress
    except ImportError:
        print("Installing waitress: pip install waitress")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "waitress"])
        import waitress

    # Open browser in background so admin doesn't have to do anything
    t = threading.Thread(target=open_browser, daemon=True)
    t.start()

    # Block here: serve the app with load balancing (multiple threads)
    waitress.serve(
        app_module.app,
        host=HOST,
        port=PORT,
        threads=THREADS,
        channel_timeout=120,
        connection_limit=1000,
        url_scheme="http",
    )


if __name__ == "__main__":
    main()
