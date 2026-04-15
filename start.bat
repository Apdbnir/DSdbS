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
echo Checking database...
python db_check.py
if %ERRORLEVEL% neq 0 (
    echo Database not found. Running database setup...
    call ..\database\setup_database.bat
    if %ERRORLEVEL% neq 0 (
        echo Database setup failed. Please fix PostgreSQL installation or run database\setup_database.bat manually.
        exit /b 1
    )
)

echo.
echo Launching server and application without opening new windows...
echo.

start "" /b /d "%~dp0backend" cmd /c "call venv\Scripts\activate && python server.py > server.log 2>&1"
start "" /b /d "%~dp0backend" cmd /c "call venv\Scripts\activate && pythonw.exe app.py > app.log 2>&1"

echo.
echo Server and application have been started in the background.
echo Logs: %~dp0backend\server.log, %~dp0backend\app.log
exit /b
