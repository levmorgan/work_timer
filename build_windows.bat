@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo No virtualenv found at .venv — please create one and install dependencies:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements-dev.txt
    exit /b 1
)

echo === 1. Running tests ===
.venv\Scripts\pytest tests/ -q

echo.
echo === 2. Cleaning previous build ===
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo === 3. Building executable with PyInstaller ===
.venv\Scripts\python -m PyInstaller pomodoro.spec

echo.
echo === Done ===
echo Executable: %cd%\dist\work_timer\work_timer.exe
dir dist\work_timer\work_timer.exe
