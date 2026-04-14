@echo off
REM ============================================================================
REM Restore Script: Restores a PostgreSQL dump to the Educational Process Database
REM ============================================================================

echo.
echo ============================================================================
echo  Database Restore
echo ============================================================================
echo.

set PG_BIN=C:\Program Files\PostgreSQL\16\bin
set PG_HOST=localhost
set PG_PORT=5432
set PG_USER=postgres
set PG_PASSWORD=postgres
set DB_NAME=educational_process

set PGPASSWORD=%PG_PASSWORD%

REM Check if backup file is provided
if "%~1"=="" (
    echo Usage: restore_database.bat ^<backup_file.sql^>
    echo.
    echo Available backups:
    dir "%~dp0..\backups\*.sql" /b 2>nul || echo No backups found
    echo.
    pause
    exit /b 1
)

set BACKUP_FILE=%~1

if not exist "%BACKUP_FILE%" (
    echo ERROR: Backup file not found: %BACKUP_FILE%
    pause
    exit /b 1
)

echo WARNING: This will DROP and RECREATE the database!
echo Backup file: %BACKUP_FILE%
echo.
set /p CONFIRM="Type 'YES' to continue: "

if "%CONFIRM%"=="YES" (
    echo.
    echo Dropping existing database...
    "%PG_BIN%\psql.exe" -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -c "DROP DATABASE IF EXISTS %DB_NAME%;"
    
    echo Creating fresh database...
    "%PG_BIN%\psql.exe" -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -c "CREATE DATABASE %DB_NAME%;"
    
    echo Restoring from backup...
    "%PG_BIN%\psql.exe" -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -d %DB_NAME% -f "%BACKUP_FILE%"
    
    if %errorlevel% equ 0 (
        echo.
        echo Database restored successfully from: %BACKUP_FILE%
    ) else (
        echo.
        echo ERROR: Restore failed
    )
) else (
    echo Restore cancelled.
)

echo.
pause
