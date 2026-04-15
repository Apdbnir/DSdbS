"""
Data Generator for Educational Process Management System
Generates English sample records for main tables: employees, students, lessons,
and association tables: student_lessons, group_lessons
"""

import os
import random
from datetime import datetime, timedelta, date, time

# Random data generators
FIRST_NAMES_MALE = [
    'James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard',
    'Charles', 'Joseph', 'Thomas', 'Christopher', 'Daniel', 'Matthew',
    'Anthony', 'Mark', 'Donald', 'Steven', 'Paul', 'Andrew', 'Joshua',
    'Kevin', 'Brian', 'George', 'Edward', 'Ronald', 'Timothy', 'Jason',
    'Jeffrey', 'Ryan', 'Jacob'
]

FIRST_NAMES_FEMALE = [
    'Mary', 'Patricia', 'Jennifer', 'Linda', 'Elizabeth', 'Barbara',
    'Susan', 'Jessica', 'Sarah', 'Karen', 'Nancy', 'Margaret', 'Lisa',
    'Betty', 'Dorothy', 'Sandra', 'Ashley', 'Kimberly', 'Donna', 'Emily',
    'Michelle', 'Carol', 'Amanda', 'Melissa', 'Deborah', 'Stephanie', 'Rebecca',
    'Sharon', 'Laura', 'Cynthia', 'Kathleen'
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
    'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
    'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin'
]

TOPICS = [
    'Safety Basics', 'Traffic Rules', 'Practical Driving', 'Vehicle Maintenance',
    'Road Signs', 'Emergency Procedures', 'Night Driving', 'Highway Driving',
    'Parking Techniques', 'Defensive Driving', 'City Driving',
    'Weather Conditions', 'First Aid', 'Driving Law', 'Exam Preparation',
    'Simulator Training', 'Manual Transmission', 'Automatic Transmission',
    'Inspection Procedure', 'Customer Service'
]

LESSON_NAMES = [
    'Classroom Session', 'Route Practice', 'Safety Briefing', 'Driving Lesson',
    'Mock Exam', 'Feedback Session', 'Vehicle Inspection', 'Simulator Practice',
    'Road Test', 'Highway Training', 'Parking Practice', 'Night Session',
    'City Route', 'Emergency Stop', 'Manual Gear Practice'
]

MEDICAL_CERTS = ['Valid Medical', 'Expired Medical', 'Pending Review', 'Not Required', 'Updated']
PASSPORT_PREFIXES = ['AA', 'BB', 'CC', 'DD', 'EE', 'FF', 'GG', 'HH', 'JJ', 'KK']

EMAIL_DOMAINS = ['@mail.ru', '@gmail.com', '@yandex.ru', '@inbox.ru', '@bk.ru']

PHONE_CODES = ['+7(900)', '+7(901)', '+7(902)', '+7(903)', '+7(905)', '+7(906)', '+7(909)', '+7(916)', '+7(926)', '+7(977)']


def generate_phone():
    return f"{random.choice(PHONE_CODES)}{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(10,99)}"

def generate_email(name):
    translit = name.split()[0].lower()
    translit = translit.replace('а', 'a').replace('е', 'e').replace('ё', 'yo').replace('и', 'i')
    translit = translit.replace('о', 'o').replace('у', 'u').replace('ы', 'y').replace('э', 'e')
    translit = translit.replace('ю', 'yu').replace('я', 'ya').replace('й', 'y')
    translit = translit.replace('ж', 'zh').replace('ц', 'ts').replace('ч', 'ch').replace('ш', 'sh')
    translit = translit.replace('щ', 'shch').replace('ъ', '').replace('ь', '')
    return f"{translit}{random.randint(1,99)}{random.choice(EMAIL_DOMAINS)}"

def generate_passport():
    return f"{random.choice(PASSPORT_PREFIXES)} {random.randint(100000, 999999)}"

def generate_date(start_year=2025, end_year=2026):
    start = date(start_year, 1, 1)
    end = date(end_year, 6, 30)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)

def generate_time():
    hour = random.choice([8, 9, 10, 11, 12, 13, 14, 15, 16, 17])
    minute = random.choice([0, 15, 30, 45])
    return time(hour, minute)


def generate_employees(count=40):
    """Generate employee records"""
    positions = list(range(1, 11))  # position_ids
    employees = []
    
    for i in range(1, count + 1):
        if i <= len(FIRST_NAMES_MALE) and i % 3 != 0:
            name = f"{LAST_NAMES[i % len(LAST_NAMES)]} {FIRST_NAMES_MALE[i-1]}"
        elif i <= len(FIRST_NAMES_FEMALE):
            name = f"{LAST_NAMES[i % len(LAST_NAMES)]} {FIRST_NAMES_FEMALE[i-1]}"
        else:
            first = random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE)
            last_name = random.choice(LAST_NAMES)
            name = f"{last_name} {first}"
        
        experience = random.randint(1, 30)
        email = generate_email(name)
        phone = generate_phone()
        position_id = random.choice(positions)
        
        employees.append((i, name, experience, email, phone, position_id))
    
    return employees


def generate_students(count=40):
    """Generate student records"""
    students = []
    
    for i in range(1, count + 1):
        first = random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE)
        last_name = random.choice(LAST_NAMES)
        full_name = f"{last_name} {first}"
        passport = generate_passport()
        med_cert = random.choice(MEDICAL_CERTS)
        age = random.randint(16, 35)
        group_id = random.randint(1, 10)  # group_ids 1-10
        
        students.append((i, passport, full_name, med_cert, age, group_id))
    
    return students


def generate_lessons(count=300, employee_ids=None):
    """Generate lesson records"""
    lessons = []
    employee_ids = employee_ids or list(range(1, 51))
    
    for i in range(1, count + 1):
        result = random.choice(['Passed', 'Failed', 'Completed', 'In progress', None, None])
        topic = random.choice(TOPICS)
        lesson_time = generate_time()
        lesson_date = generate_date()
        name = random.choice(LESSON_NAMES)
        contact_email = random.choice([None, None, generate_email(random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE))])
        location_id = random.randint(1, 10)
        vehicle_id = random.choice([None, None, None, random.randint(1, 10)])  # 70% no vehicle
        format_id = random.randint(1, 4)
        employee_id = random.choice(employee_ids)
        
        lessons.append((i, result, topic, lesson_time, lesson_date, name, contact_email, 
                       location_id, vehicle_id, format_id, employee_id))
    
    return lessons


def generate_student_lessons(student_ids, lesson_ids, avg_lessons_per_student=5):
    """Generate student-lesson associations"""
    associations = set()
    
    for student_id in student_ids:
        num_lessons = random.randint(2, avg_lessons_per_student + 2)
        selected_lessons = random.sample(lesson_ids, min(num_lessons, len(lesson_ids)))
        for lesson_id in selected_lessons:
            associations.add((student_id, lesson_id))
    
    return list(associations)


def generate_group_lessons(group_ids, lesson_ids, avg_lessons_per_group=15):
    """Generate group-lesson associations"""
    associations = set()
    
    for group_id in group_ids:
        num_lessons = random.randint(10, avg_lessons_per_group + 10)
        selected_lessons = random.sample(lesson_ids, min(num_lessons, len(lesson_ids)))
        for lesson_id in selected_lessons:
            associations.add((group_id, lesson_id))
    
    return list(associations)


def generate_sql_inserts(output_file=None):
    """Generate SQL INSERT statements for all main tables"""
    
    if output_file is None:
        output_file = os.path.join(os.path.dirname(__file__), 'populate_main_tables.sql')
    
    random.seed(42)  # Reproducible results
    
    employees = generate_employees(40)
    students = generate_students(40)
    lessons = generate_lessons(40, employee_ids=list(range(1, 41)))
    
    student_ids = list(range(1, 41))
    lesson_ids = list(range(1, 41))
    group_ids = list(range(1, 11))
    
    student_lessons = generate_student_lessons(student_ids, lesson_ids)
    group_lessons = generate_group_lessons(group_ids, lesson_ids)
    
    sql_lines = []
    sql_lines.append("-- ============================================================================")
    sql_lines.append("-- Auto-generated data for main tables")
    sql_lines.append("-- Generated by: data_generator.py")
    sql_lines.append(f"-- Generation date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_lines.append("-- ============================================================================\n")
    
    # Employees
    sql_lines.append("-- ============================================================================")
    sql_lines.append("-- Employees (Сотрудники)")
    sql_lines.append("-- ============================================================================\n")
    sql_lines.append("INSERT INTO public.employees (id, name, experience, email, phone, position_id) VALUES")
    
    emp_values = []
    for emp in employees:
        emp_values.append(f"({emp[0]}, '{emp[1]}', {emp[2]}, '{emp[3]}', '{emp[4]}', {emp[5]})")
    sql_lines.append(',\n'.join(emp_values) + ';')
    sql_lines.append(f"\nSELECT setval('public.employees_id_seq', (SELECT MAX(id) FROM public.employees));\n")
    
    # Students
    sql_lines.append("-- ============================================================================")
    sql_lines.append("-- Students (Ученики/Курсанты)")
    sql_lines.append("-- ============================================================================\n")
    sql_lines.append("INSERT INTO public.students (id, passport_number, full_name, medical_certificate, age, group_id) VALUES")
    
    student_values = []
    for student in students:
        student_values.append(f"({student[0]}, '{student[1]}', '{student[2]}', '{student[3]}', {student[4]}, {student[5]})")
    sql_lines.append(',\n'.join(student_values) + ';')
    sql_lines.append(f"\nSELECT setval('public.students_id_seq', (SELECT MAX(id) FROM public.students));\n")
    
    # Lessons
    sql_lines.append("-- ============================================================================")
    sql_lines.append("-- Lessons (Занятия)")
    sql_lines.append("-- ============================================================================\n")
    sql_lines.append("INSERT INTO public.lessons (id, result, topic, lesson_time, lesson_date, name, contact_email, location_id, vehicle_id, format_id, employee_id) VALUES")
    
    lesson_values = []
    for lesson in lessons:
        result_val = f"'{lesson[1]}'" if lesson[1] else 'NULL'
        contact_val = f"'{lesson[6]}'" if lesson[6] else 'NULL'
        vehicle_val = lesson[8] if lesson[8] else 'NULL'
        lesson_values.append(
            f"({lesson[0]}, {result_val}, '{lesson[2]}', '{lesson[3].strftime('%H:%M:%S')}', "
            f"'{lesson[4].isoformat()}', '{lesson[5]}', {contact_val}, {lesson[7]}, "
            f"{vehicle_val}, {lesson[9]}, {lesson[10]})"
        )
    sql_lines.append(',\n'.join(lesson_values) + ';')
    sql_lines.append(f"\nSELECT setval('public.lessons_id_seq', (SELECT MAX(id) FROM public.lessons));\n")
    
    # Student-Lessons
    sql_lines.append("-- ============================================================================")
    sql_lines.append("-- Student-Lesson Associations (Ученик-Занятия)")
    sql_lines.append("-- ============================================================================\n")
    sql_lines.append("INSERT INTO public.student_lessons (student_id, lesson_id) VALUES")
    
    sl_values = []
    for sl in student_lessons:
        sl_values.append(f"({sl[0]}, {sl[1]})")
    sql_lines.append(',\n'.join(sl_values) + ';\n')
    
    # Group-Lessons
    sql_lines.append("-- ============================================================================")
    sql_lines.append("-- Group-Lesson Associations (Группа-Занятия)")
    sql_lines.append("-- ============================================================================\n")
    sql_lines.append("INSERT INTO public.group_lessons (group_id, lesson_id) VALUES")
    
    gl_values = []
    for gl in group_lessons:
        gl_values.append(f"({gl[0]}, {gl[1]})")
    sql_lines.append(',\n'.join(gl_values) + ';\n')
    
    # Summary
    sql_lines.append("-- ============================================================================")
    sql_lines.append("-- Summary")
    sql_lines.append("-- ============================================================================")
    sql_lines.append(f"-- Employees: {len(employees)}")
    sql_lines.append(f"-- Students: {len(students)}")
    sql_lines.append(f"-- Lessons: {len(lessons)}")
    sql_lines.append(f"-- Student-Lesson associations: {len(student_lessons)}")
    sql_lines.append(f"-- Group-Lesson associations: {len(group_lessons)}")
    sql_lines.append("-- ============================================================================\n")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))
    
    print(f"SQL file generated: {output_file}")
    print(f"  Employees: {len(employees)}")
    print(f"  Students: {len(students)}")
    print(f"  Lessons: {len(lessons)}")
    print(f"  Student-Lesson associations: {len(student_lessons)}")
    print(f"  Group-Lesson associations: {len(group_lessons)}")


if __name__ == '__main__':
    generate_sql_inserts()
