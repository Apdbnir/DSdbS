@echo off
REM ============================================================================
REM Quick Verification Script - Tests database setup
REM ============================================================================

echo.
echo ============================================================================
echo  Database Verification
echo ============================================================================
echo.

set PG_BIN=C:\Program Files\PostgreSQL\16\bin
set PG_HOST=localhost
set PG_PORT=5432
set PG_USER=postgres
set PG_PASSWORD=postgres
set DB_NAME=driving_school

set PGPASSWORD=%PG_PASSWORD%

echo Checking database existence...
"%PG_BIN%\psql.exe" -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -d %DB_NAME% -c "SELECT current_database();" 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Database '%DB_NAME%' not found!
    echo Please run setup_database.bat first.
    pause
    exit /b 1
)

echo.
echo Checking tables...
"%PG_BIN%\psql.exe" -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -d %DB_NAME% -c "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"

echo.
echo Checking record counts...
"%PG_BIN%\psql.exe" -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -d %DB_NAME% -c "SELECT 'positions' as table_name, COUNT(*) as count FROM positions UNION ALL SELECT 'lesson_formats', COUNT(*) FROM lesson_formats UNION ALL SELECT 'locations', COUNT(*) FROM locations UNION ALL SELECT 'vehicles', COUNT(*) FROM vehicles UNION ALL SELECT 'groups', COUNT(*) FROM groups UNION ALL SELECT 'employees', COUNT(*) FROM employees UNION ALL SELECT 'students', COUNT(*) FROM students UNION ALL SELECT 'lessons', COUNT(*) FROM lessons UNION ALL SELECT 'student_lessons', COUNT(*) FROM student_lessons UNION ALL SELECT 'group_lessons', COUNT(*) FROM group_lessons ORDER BY table_name;"

echo.
echo Checking views...
"%PG_BIN%\psql.exe" -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -d %DB_NAME% -c "SELECT viewname FROM pg_views WHERE schemaname='public';"

echo.
echo Checking functions...
"%PG_BIN%\psql.exe" -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -d %DB_NAME% -c "SELECT routine_name FROM information_schema.routines WHERE routine_schema='public' AND routine_type='FUNCTION';"

echo.
echo Checking triggers...
"%PG_BIN%\psql.exe" -U %PG_USER% -h %PG_HOST% -p %PG_PORT% -d %DB_NAME% -c "SELECT trigger_name, event_object_table FROM information_schema.triggers WHERE trigger_schema='public';"

echo.
echo ============================================================================
echo  Verification Complete!
echo ============================================================================
echo.
pause
