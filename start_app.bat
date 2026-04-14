@echo off
REM ============================================================================
REM Start Desktop Application (PyQt6)
REM ============================================================================

echo.
echo ============================================================================
echo  Starting Driving School Management System
echo ============================================================================
echo.

cd /d "%~dp0backend"

REM Create virtual environment if not exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate

echo Installing dependencies...
pip install --upgrade -r requirements.txt

echo.
echo Starting desktop application...
echo.

python app.py

pause
