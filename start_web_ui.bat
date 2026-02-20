@echo off
REM OpenClass Nexus AI - Web UI Launcher for Windows
REM Double-click file ini untuk menjalankan Web UI

echo ============================================================
echo   OpenClass Nexus AI - Web UI Launcher
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak ditemukan!
    echo.
    echo Silakan install Python terlebih dahulu:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [OK] Python ditemukan
echo.

REM Check if virtual environment exists
if exist "openclass-env\Scripts\activate.bat" (
    echo [INFO] Mengaktifkan virtual environment...
    call openclass-env\Scripts\activate.bat
    echo [OK] Virtual environment aktif
    echo.
) else (
    echo [WARNING] Virtual environment tidak ditemukan
    echo [INFO] Menggunakan Python global
    echo.
)

REM Run the startup script
echo [INFO] Menjalankan pre-flight checks...
echo.
python scripts\start_web_ui.py

REM If script exits, pause to show any error messages
if errorlevel 1 (
    echo.
    echo [ERROR] Terjadi kesalahan saat menjalankan server
    echo.
    pause
)
