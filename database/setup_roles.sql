-- ============================================================================
-- Setup Script: Creates database, roles, schema, and populates data
-- Run on Windows with PostgreSQL installed
-- Usage: psql -U postgres -f setup_database.bat (or run setup_database.bat)
-- ============================================================================

-- Create roles
DO $$
BEGIN
    -- Create regular user role if not exists
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user WITH LOGIN PASSWORD 'user123';
    END IF;
    
    -- Create superuser role if not exists
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_superuser') THEN
        CREATE ROLE app_superuser WITH LOGIN PASSWORD '1234567890' SUPERUSER;
    END IF;
END
$$;

-- Create database
SELECT 'CREATE DATABASE educational_process' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'educational_process')\gexec
