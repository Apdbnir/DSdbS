@echo off
REM ============================================================================
REM Start Server Script
REM ============================================================================

echo.
echo ============================================================================
echo  Starting Educational Process Management System Server
echo ============================================================================
echo.

cd /d "%~dp0backend"

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

echo.
echo Starting server on http://localhost:8080
echo Press Ctrl+C to stop the server
echo.

python server.py

pause
