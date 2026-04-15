@echo off
REM ============================================================================
REM Start both the Educational Process Management System Server and Desktop App
REM ============================================================================

echo.
echo ============================================================================
echo  Starting Driving School Management System
echo ============================================================================
echo.

cd /d "%~dp0backend"

REM Create virtual environment if it does not exist
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate
echo Installing dependencies...
pip install --upgrade -r requirements.txt

echo.
echo Launching server and application in separate windows...

start "Driving School Server" cmd /k "cd /d "%~dp0backend" && call venv\Scripts\activate && python server.py"
start "Driving School App" cmd /k "cd /d "%~dp0backend" && call venv\Scripts\activate && python app.py"

echo.
echo Server and application have been started.
echo Close these windows to stop each component.
pause
