@echo off
REM PDF Data Extractor - Windows Launcher
REM Double-click this file to start the web interface

title PDF Census Data Extractor

echo =========================================
echo   PDF Census Data Extractor
echo   Starting web interface...
echo =========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    echo.
    echo Please install Python from:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [*] Setting up virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
    echo.
)

REM Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo.
echo [*] Installing dependencies...
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt

echo.
echo =========================================
echo   [OK] Setup complete!
echo =========================================
echo.
echo [*] Starting web interface...
echo.
echo The app will open in your browser at:
echo     http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.
echo =========================================
echo.

REM Launch Streamlit
streamlit run app.py

REM Deactivate virtual environment on exit
call venv\Scripts\deactivate.bat

pause
