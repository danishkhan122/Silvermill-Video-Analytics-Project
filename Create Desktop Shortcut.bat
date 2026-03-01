@echo off
title Create SilverMill Desktop Shortcut
cd /d "%~dp0"

echo Creating application icon...
set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY where python >nul 2>nul && set "PY=python"

if not defined PY (
    echo Python not found. Skipping icon creation.
) else (
    "%PY%" create_icon.py
)

echo.
echo Creating shortcut on Desktop...
powershell -NoProfile -ExecutionPolicy Bypass -File "Create-DesktopShortcut.ps1" "%~dp0"

echo.
echo Done. Look for "SilverMill" on your Desktop.
pause
