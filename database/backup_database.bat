@echo off
REM ============================================================================
REM Backup Script: Creates a PostgreSQL dump of the Educational Process Database
REM ============================================================================

echo.
echo ============================================================================
echo  Database Backup
echo ============================================================================
echo.

set PG_BIN=C:\Program Files\PostgreSQL\16\bin
set PG_HOST=localhost
set PG_PORT=5432
set PG_USER=postgres
set PG_PASSWORD=postgres
set DB_NAME=driving_school

set PGPASSWORD=%PG_PASSWORD%

REM Create backup directory if it doesn't exist
if not exist "%~dp0..\backups" mkdir "%~dp0..\backups"

REM Generate timestamp for filename
set TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

set BACKUP_FILE=%~dp0..\backups\%DB_NAME%_%TIMESTAMP%.sql

echo Creating backup: %BACKUP_FILE%

"%PG_BIN%\pg_dump.exe" -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -d %DB_NAME% -F p -f "%BACKUP_FILE%"

if %errorlevel% equ 0 (
    echo.
    echo Backup created successfully: %BACKUP_FILE%
) else (
    echo.
    echo ERROR: Backup failed
)

echo.
pause
