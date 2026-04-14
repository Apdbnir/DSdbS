@echo off
REM ============================================================================
REM Windows Setup Script: Creates and populates the Educational Process Database
REM Requirements: PostgreSQL installed and running
REM Usage: Run as administrator or ensure PostgreSQL user has CREATE DATABASE rights
REM ============================================================================

echo.
echo ============================================================================
echo  Educational Process Management System - Database Setup
echo ============================================================================
echo.

REM Set PostgreSQL bin path (adjust if needed)
set PG_BIN=C:\Program Files\PostgreSQL\16\bin
set PG_HOST=localhost
set PG_PORT=5432
set PG_USER=postgres
set PG_PASSWORD=postgres
set DB_NAME=educational_process

REM Check if psql exists
if not exist "%PG_BIN%\psql.exe" (
    echo ERROR: psql.exe not found at %PG_BIN%
    echo Please update the PG_BIN path in this script to point to your PostgreSQL installation.
    echo Common paths:
    echo   C:\Program Files\PostgreSQL\16\bin
    echo   C:\Program Files\PostgreSQL\15\bin
    echo   C:\Program Files\PostgreSQL\14\bin
    pause
    exit /b 1
)

REM Set password for psql
set PGPASSWORD=%PG_PASSWORD%

echo [1/5] Creating database...
"%PG_BIN%\psql.exe" -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -c "SELECT 'CREATE DATABASE %DB_NAME%' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '%DB_NAME%')\gexec"
if %errorlevel% neq 0 (
    echo ERROR: Failed to create database
    pause
    exit /b 1
)
echo Database created successfully.

echo.
echo [2/5] Creating schema (tables, constraints, indexes, views)...
"%PG_BIN%\psql.exe" -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -d %DB_NAME% -f "%~dp0create_schema.sql"
if %errorlevel% neq 0 (
    echo ERROR: Failed to create schema
    pause
    exit /b 1
)
echo Schema created successfully.

echo.
echo [3/5] Seeding lookup tables (positions, formats, locations, vehicles, groups)...
"%PG_BIN%\psql.exe" -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -d %DB_NAME% -f "%~dp0seed_lookup_tables.sql"
if %errorlevel% neq 0 (
    echo ERROR: Failed to seed lookup tables
    pause
    exit /b 1
)
echo Lookup tables seeded successfully.

echo.
echo [4/5] Generating and populating main tables data...
echo Running data generator...
python "%~dp0data_generator.py"
if %errorlevel% neq 0 (
    echo ERROR: Failed to run data generator
    pause
    exit /b 1
)

echo Populating main tables...
"%PG_BIN%\psql.exe" -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -d %DB_NAME% -f "%~dp0populate_main_tables.sql"
if %errorlevel% neq 0 (
    echo ERROR: Failed to populate main tables
    pause
    exit /b 1
)
echo Main tables populated successfully.

echo.
echo [5/5] Creating functions, triggers, and views...
"%PG_BIN%\psql.exe" -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -d %DB_NAME% -f "%~dp0create_functions_triggers.sql"
if %errorlevel% neq 0 (
    echo ERROR: Failed to create functions and triggers
    pause
    exit /b 1
)
echo Functions and triggers created successfully.

echo.
echo ============================================================================
echo  Database setup complete!
echo ============================================================================
echo.
echo Database: %DB_NAME%
echo Host: %PG_HOST%
echo Port: %PG_PORT%
echo User: %PG_USER%
echo.
echo Tables created:
echo   - positions (10 records)
echo   - lesson_formats (4 records)
echo   - locations (10 records)
echo   - vehicles (10 records)
echo   - groups (10 records)
echo   - employees (50 records)
echo   - cadets (200 records)
echo   - lessons (300 records)
echo   - cadet_lessons (900+ associations)
echo   - group_lessons (170+ associations)
echo.
echo Views:
echo   - v_lessons_full
echo   - v_cadets_full
echo   - v_employees_full
echo.
echo Triggers:
echo   - trg_validate_cadet_age
echo   - trg_validate_format_location
echo.
echo To verify, run: "%PG_BIN%\psql.exe" -U %PG_USER% -d %DB_NAME% -c "SELECT * FROM public.v_lessons_full LIMIT 5;"
echo.
pause
