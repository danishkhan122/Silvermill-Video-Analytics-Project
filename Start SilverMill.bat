@echo off
title SilverMill
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY where python >nul 2>nul && set "PY=python"

if not defined PY (
    echo Python was not found. Please install Python and add it to PATH.
    echo Or open a terminal in this folder and run: py launcher.py
    pause
    exit /b 1
)

"%PY%" launcher.py

if errorlevel 1 (
    echo.
    echo SilverMill could not start. Try running from terminal:
    echo   pip install -r requirements.txt
    echo   %PY% launcher.py
    pause
)
