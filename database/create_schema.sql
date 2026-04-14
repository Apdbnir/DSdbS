-- ============================================================================
-- Database Schema: Driving School Database System (Система управления автошколой)
-- Database: PostgreSQL
-- Description: Database for managing driving school (students, instructors,
--              groups, driving lessons, vehicles, locations, schedules, etc.)
-- ============================================================================

-- Drop existing tables if they exist
DROP TABLE IF EXISTS public.students CASCADE;
DROP TABLE IF EXISTS public.employees CASCADE;
DROP TABLE IF EXISTS public.groups CASCADE;
DROP TABLE IF EXISTS public.lessons CASCADE;
DROP TABLE IF EXISTS public.positions CASCADE;
DROP TABLE IF EXISTS public.locations CASCADE;
DROP TABLE IF EXISTS public.vehicles CASCADE;
DROP TABLE IF EXISTS public.lesson_formats CASCADE;
DROP TABLE IF EXISTS public.student_lessons CASCADE;
DROP TABLE IF EXISTS public.group_lessons CASCADE;

-- ============================================================================
-- LOOKUP TABLES (Справочники) - Only superuser can modify
-- ============================================================================

-- Table: positions (Должности)
CREATE TABLE IF NOT EXISTS public.positions
(
    id BIGSERIAL NOT NULL,
    name character varying(100) NOT NULL,
    phone character varying(20),
    employment_type character varying(50) NOT NULL DEFAULT 'Полная занятость',
    notes text,
    PRIMARY KEY (id)
);

-- Table: lesson_formats (Форма реализации)
CREATE TABLE IF NOT EXISTS public.lesson_formats
(
    id BIGSERIAL NOT NULL,
    name character varying(50) NOT NULL,
    PRIMARY KEY (id)
);

-- Table: locations (Место проведения)
CREATE TABLE IF NOT EXISTS public.locations
(
    id BIGSERIAL NOT NULL,
    geolocation character varying(200),
    location_type character varying(50) NOT NULL,
    address character varying(200) NOT NULL,
    responsible_employee_id bigint,
    PRIMARY KEY (id)
);

-- Table: vehicles (Автомобиль)
CREATE TABLE IF NOT EXISTS public.vehicles
(
    id BIGSERIAL NOT NULL,
    vehicle_number character varying(20) NOT NULL,
    route character varying(200),
    notes text,
    category character varying(20),
    PRIMARY KEY (id)
);

-- ============================================================================
-- MAIN TABLES (Основные таблицы)
-- ============================================================================

-- Table: employees (Сотрудник/Инструктор)
CREATE TABLE IF NOT EXISTS public.employees
(
    id BIGSERIAL NOT NULL,
    name character varying(150) NOT NULL,
    experience integer,
    email character varying(100),
    phone character varying(20),
    position_id bigint,
    PRIMARY KEY (id)
);

-- Table: groups (Группа)
CREATE TABLE IF NOT EXISTS public.groups
(
    id BIGSERIAL NOT NULL,
    group_number character varying(20) NOT NULL,
    room_number character varying(20),
    format_type character varying(50),
    PRIMARY KEY (id)
);

-- Table: students (Ученик/Курсант)
CREATE TABLE IF NOT EXISTS public.students
(
    id BIGSERIAL NOT NULL,
    passport_number character varying(20) NOT NULL,
    full_name character varying(150) NOT NULL,
    medical_certificate character varying(50),
    age integer NOT NULL,
    group_id bigint,
    PRIMARY KEY (id)
);

-- Table: lessons (Занятия по вождению)
CREATE TABLE IF NOT EXISTS public.lessons
(
    id BIGSERIAL NOT NULL,
    result text,
    topic character varying(200),
    lesson_time time NOT NULL,
    lesson_date date NOT NULL,
    name character varying(200) NOT NULL,
    contact_email character varying(100),
    location_id bigint,
    vehicle_id bigint,
    format_id bigint,
    employee_id bigint,
    PRIMARY KEY (id)
);

-- ============================================================================
-- ASSOCIATION TABLES (Таблицы связей)
-- ============================================================================

-- Table: student_lessons (Ученик-Занятия) - Many-to-Many
CREATE TABLE IF NOT EXISTS public.student_lessons
(
    student_id bigint NOT NULL,
    lesson_id bigint NOT NULL,
    PRIMARY KEY (student_id, lesson_id)
);

-- Table: group_lessons (Группа-Занятия) - Many-to-Many
CREATE TABLE IF NOT EXISTS public.group_lessons
(
    group_id bigint NOT NULL,
    lesson_id bigint NOT NULL,
    PRIMARY KEY (group_id, lesson_id)
);

-- ============================================================================
-- FOREIGN KEY CONSTRAINTS
-- ============================================================================

ALTER TABLE IF EXISTS public.employees
    ADD CONSTRAINT fk_employees_positions FOREIGN KEY (position_id)
    REFERENCES public.positions (id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE IF EXISTS public.locations
    ADD CONSTRAINT fk_locations_responsible_employee FOREIGN KEY (responsible_employee_id)
    REFERENCES public.employees (id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE IF EXISTS public.students
    ADD CONSTRAINT fk_students_groups FOREIGN KEY (group_id)
    REFERENCES public.groups (id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE IF EXISTS public.lessons
    ADD CONSTRAINT fk_lessons_location FOREIGN KEY (location_id)
    REFERENCES public.locations (id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE IF EXISTS public.lessons
    ADD CONSTRAINT fk_lessons_vehicle FOREIGN KEY (vehicle_id)
    REFERENCES public.vehicles (id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE IF EXISTS public.lessons
    ADD CONSTRAINT fk_lessons_format FOREIGN KEY (format_id)
    REFERENCES public.lesson_formats (id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE IF EXISTS public.lessons
    ADD CONSTRAINT fk_lessons_employee FOREIGN KEY (employee_id)
    REFERENCES public.employees (id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE IF EXISTS public.student_lessons
    ADD CONSTRAINT fk_student_lessons_student FOREIGN KEY (student_id)
    REFERENCES public.students (id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE IF EXISTS public.student_lessons
    ADD CONSTRAINT fk_student_lessons_lesson FOREIGN KEY (lesson_id)
    REFERENCES public.lessons (id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE IF EXISTS public.group_lessons
    ADD CONSTRAINT fk_group_lessons_group FOREIGN KEY (group_id)
    REFERENCES public.groups (id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE IF EXISTS public.group_lessons
    ADD CONSTRAINT fk_group_lessons_lesson FOREIGN KEY (lesson_id)
    REFERENCES public.lessons (id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_employees_position ON public.employees(position_id);
CREATE INDEX IF NOT EXISTS idx_students_group ON public.students(group_id);
CREATE INDEX IF NOT EXISTS idx_lessons_location ON public.lessons(location_id);
CREATE INDEX IF NOT EXISTS idx_lessons_vehicle ON public.lessons(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_lessons_format ON public.lessons(format_id);
CREATE INDEX IF NOT EXISTS idx_lessons_employee ON public.lessons(employee_id);
CREATE INDEX IF NOT EXISTS idx_lessons_date ON public.lessons(lesson_date);
CREATE INDEX IF NOT EXISTS idx_locations_responsible ON public.locations(responsible_employee_id);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Complete lesson information
CREATE OR REPLACE VIEW public.v_lessons_full AS
SELECT
    l.id,
    l.name AS lesson_name,
    l.topic,
    l.lesson_date,
    l.lesson_time,
    l.result,
    lf.name AS format_name,
    loc.address AS location_address,
    v.vehicle_number,
    e.name AS employee_name
FROM public.lessons l
LEFT JOIN public.lesson_formats lf ON l.format_id = lf.id
LEFT JOIN public.locations loc ON l.location_id = loc.id
LEFT JOIN public.vehicles v ON l.vehicle_id = v.id
LEFT JOIN public.employees e ON l.employee_id = e.id;

-- View: Students with group information
CREATE OR REPLACE VIEW public.v_students_full AS
SELECT
    s.id,
    s.full_name,
    s.passport_number,
    s.medical_certificate,
    s.age,
    g.group_number,
    g.format_type AS group_format
FROM public.students s
LEFT JOIN public.groups g ON s.group_id = g.id;

-- View: Employees with position information
CREATE OR REPLACE VIEW public.v_employees_full AS
SELECT
    e.id,
    e.name,
    e.experience,
    e.email,
    e.phone,
    p.name AS position_name,
    p.employment_type
FROM public.employees e
LEFT JOIN public.positions p ON e.position_id = p.id;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE positions IS 'Должности - Position lookup table (superuser only)';
COMMENT ON TABLE lesson_formats IS 'Форма реализации - Lesson format lookup table (superuser only)';
COMMENT ON TABLE locations IS 'Место проведения - Location lookup table (superuser only)';
COMMENT ON TABLE vehicles IS 'Автомобиль - Vehicle lookup table (superuser only)';
COMMENT ON TABLE employees IS 'Сотрудник/Инструктор - Employee table';
COMMENT ON TABLE groups IS 'Группа - Group lookup table (superuser only)';
COMMENT ON TABLE students IS 'Ученик/Курсант - Student table';
COMMENT ON TABLE lessons IS 'Занятия - Lesson table (main operational table)';
COMMENT ON TABLE student_lessons IS 'Ученик-Занятия - Student-Lesson association table';
COMMENT ON TABLE group_lessons IS 'Группа-Занятия - Group-Lesson association table';
