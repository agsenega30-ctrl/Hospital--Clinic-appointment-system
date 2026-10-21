@echo off
title Hospital Appointment System
echo ========================================================
echo   Starting Hospital ^& Clinic Appointment System...
echo ========================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv .venv
    echo and then: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo [*] Checking database seed...
.venv\Scripts\python.exe seed.py

echo.
echo [*] Launching Flask server on http://127.0.0.1:5000 ...
echo [*] Press Ctrl+C in this window anytime to stop the server.
echo.

start "" http://127.0.0.1:5000
.venv\Scripts\python.exe app.py

pause
