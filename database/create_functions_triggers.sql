-- ============================================================================
-- Triggers, Functions, and Operators
-- ============================================================================

-- Function: Auto-update timestamp on lesson modification
CREATE OR REPLACE FUNCTION public.update_modified_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function: Validate student age (must be >= 16)
CREATE OR REPLACE FUNCTION public.validate_student_age()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.age < 16 THEN
        RAISE EXCEPTION 'Student age must be at least 16, got %', NEW.age;
    END IF;
    IF NEW.age > 100 THEN
        RAISE EXCEPTION 'Student age seems invalid (>%): %', 100, NEW.age;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function: Validate lesson format compatibility with location
CREATE OR REPLACE FUNCTION public.validate_lesson_format_location()
RETURNS TRIGGER AS $$
DECLARE
    format_name VARCHAR;
    loc_type VARCHAR;
BEGIN
    -- Get format name
    SELECT name INTO format_name FROM public.lesson_formats WHERE id = NEW.format_id;
    
    -- Get location type if location is specified
    IF NEW.location_id IS NOT NULL THEN
        SELECT location_type INTO loc_type FROM public.locations WHERE id = NEW.location_id;
        
        -- Validate: "Online" should use "Online Platform"
        IF format_name = 'Online' AND loc_type != 'Online Platform' THEN
            RAISE WARNING 'Format "Online" typically uses "Online Platform" location type';
        END IF;
        
        -- Validate: "Classroom" should not use "Online Platform"
        IF format_name = 'Classroom' AND loc_type = 'Online Platform' THEN
            RAISE WARNING 'Format "Classroom" should not use "Online Platform" location type';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function: Count students in a lesson
CREATE OR REPLACE FUNCTION public.count_students_in_lesson(lesson_id_param BIGINT)
RETURNS INTEGER AS $$
DECLARE
    student_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO student_count
    FROM public.student_lessons
    WHERE lesson_id = lesson_id_param;
    
    RETURN student_count;
END;
$$ LANGUAGE plpgsql;

-- Function: Get lessons by date range
CREATE OR REPLACE FUNCTION public.get_lessons_by_date_range(
    start_date DATE,
    end_date DATE
)
RETURNS TABLE(
    lesson_id BIGINT,
    lesson_name VARCHAR,
    topic VARCHAR,
    lesson_date DATE,
    lesson_time TIME,
    format_name VARCHAR,
    employee_name VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        l.id,
        l.name,
        l.topic,
        l.lesson_date,
        l.lesson_time,
        lf.name,
        e.name
    FROM public.lessons l
    LEFT JOIN public.lesson_formats lf ON l.format_id = lf.id
    LEFT JOIN public.employees e ON l.employee_id = e.id
    WHERE l.lesson_date BETWEEN start_date AND end_date
    ORDER BY l.lesson_date, l.lesson_time;
END;
$$ LANGUAGE plpgsql;

-- Function: Get students by group
CREATE OR REPLACE FUNCTION public.get_students_by_group(group_id_param BIGINT)
RETURNS TABLE(
    student_id BIGINT,
    full_name VARCHAR,
    passport_number VARCHAR,
    age INTEGER,
    group_number VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id,
        s.full_name,
        s.passport_number,
        s.age,
        g.group_number
    FROM public.students s
    LEFT JOIN public.groups g ON s.group_id = g.id
    WHERE s.group_id = group_id_param
    ORDER BY s.full_name;
END;
$$ LANGUAGE plpgsql;

-- Function: Get employee workload (number of lessons)
CREATE OR REPLACE FUNCTION public.get_employee_workload()
RETURNS TABLE(
    employee_id BIGINT,
    employee_name VARCHAR,
    position_name VARCHAR,
    total_lessons BIGINT,
    unique_topics BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.name,
        p.name,
        COUNT(DISTINCT l.id) as total_lessons,
        COUNT(DISTINCT l.topic) as unique_topics
    FROM public.employees e
    LEFT JOIN public.positions p ON e.position_id = p.id
    LEFT JOIN public.lessons l ON e.id = l.employee_id
    GROUP BY e.id, e.name, p.name
    ORDER BY total_lessons DESC;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Validate student age before insert/update
DROP TRIGGER IF EXISTS trg_validate_student_age ON public.students;
DROP TRIGGER IF EXISTS trg_validate_cadet_age ON public.students;
CREATE TRIGGER trg_validate_student_age
    BEFORE INSERT OR UPDATE ON public.students
    FOR EACH ROW
    EXECUTE FUNCTION public.validate_student_age();

-- Trigger: Validate lesson format/location compatibility
DROP TRIGGER IF EXISTS trg_validate_format_location ON public.lessons;
CREATE TRIGGER trg_validate_format_location
    BEFORE INSERT OR UPDATE ON public.lessons
    FOR EACH ROW
    EXECUTE FUNCTION public.validate_lesson_format_location();

-- ============================================================================
-- Custom operators (example: ILIKE for case-insensitive search)
-- ============================================================================

-- Create a helper function for searching students by name (case-insensitive)
CREATE OR REPLACE FUNCTION public.search_students(search_term VARCHAR)
RETURNS TABLE(
    id BIGINT,
    full_name VARCHAR,
    passport_number VARCHAR,
    group_number VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id,
        s.full_name,
        s.passport_number,
        g.group_number
    FROM public.students s
    LEFT JOIN public.groups g ON s.group_id = g.id
    WHERE s.full_name ILIKE '%' || search_term || '%'
       OR s.passport_number ILIKE '%' || search_term || '%'
    ORDER BY s.full_name;
END;
$$ LANGUAGE plpgsql;

-- Create a helper function for searching employees by name (case-insensitive)
CREATE OR REPLACE FUNCTION public.search_employees(search_term VARCHAR)
RETURNS TABLE(
    id BIGINT,
    name VARCHAR,
    position_name VARCHAR,
    email VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.name,
        p.name,
        e.email
    FROM public.employees e
    LEFT JOIN public.positions p ON e.position_id = p.id
    WHERE e.name ILIKE '%' || search_term || '%'
       OR e.email ILIKE '%' || search_term || '%'
    ORDER BY e.name;
END;
$$ LANGUAGE plpgsql;
