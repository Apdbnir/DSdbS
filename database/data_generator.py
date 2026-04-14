"""
Data Generator for Educational Process Management System
Generates hundreds of records for main tables: employees, cadets, lessons, 
and association tables: cadet_lessons, group_lessons
"""

import random
from datetime import datetime, timedelta, date, time

# Random data generators
FIRST_NAMES_MALE = [
    'Иванов Алексей', 'Петров Дмитрий', 'Сидоров Сергей', 'Козлов Андрей',
    'Новиков Николай', 'Морозов Павел', 'Волков Игорь', 'Соколов Максим',
    'Лебедев Юрий', 'Егоров Артём', 'Попов Владимир', 'Кузнецов Денис',
    'Смирнов Олег', 'Васильев Игорь', 'Павлов Александр', 'Семёнов Роман',
    'Голубев Виктор', 'Виноградов Тимур', 'Богданов Илья', 'Воробьёв Фёдор',
    'Фёдоров Михаил', 'Михайлов Сергей', 'Беляев Андрей', 'Тарасов Олег',
    'Белов Дмитрий', 'Комаров Никита', 'Орлов Владислав', 'Киселёв Георгий',
    'Макаров Антон', 'Андреев Вадим'
]

FIRST_NAMES_FEMALE = [
    'Иванова Мария', 'Петрова Анна', 'Сидорова Елена', 'Козлова Ольга',
    'Новикова Татьяна', 'Морозова Наталья', 'Волкова Ирина', 'Соколова Светлана',
    'Лебедева Юлия', 'Егорова Екатерина', 'Попова Валентина', 'Кузнецова Дарья',
    'Смирнова Виктория', 'Васильева Алина', 'Павлова Ксения', 'Семёнова Полина',
    'Голубева Вера', 'Виноградова Лариса', 'Богданова Надежда', 'Воробьёва Галина',
    'Фёдорова Тамара', 'Михайлова Людмила', 'Беляева Зинаида', 'Тарасова Марина',
    'Белова Жанна', 'Комарова Оксана', 'Орлова Регина', 'Киселёва Валерия',
    'Макарова Кристина', 'Андреева Диана'
]

LAST_NAMES = [
    'Иванов', 'Петров', 'Сидоров', 'Козлов', 'Новиков', 'Морозов', 'Волков',
    'Соколов', 'Лебедев', 'Егоров', 'Попов', 'Кузнецов', 'Смирнов', 'Васильев',
    'Павлов', 'Семёнов', 'Голубев', 'Виноградов', 'Богданов', 'Воробьёв'
]

TOPICS = [
    'Введение в специальность', 'Основы безопасности', 'Теоретические основы',
    'Практические навыки', 'Лабораторная работа №1', 'Лабораторная работа №2',
    'Контрольная работа', 'Семинар по дисциплине', 'Зачётное занятие',
    'Подготовка к экзамену', 'Разбор典型ных ошибок', 'Дополнительные материалы',
    'Самостоятельная работа', 'Групповой проект', 'Индивидуальное задание',
    'Практикум по вождению', 'Основы управления ТС', 'ПДД: теория',
    'ПДД: практическое применение', 'Первая медицинская помощь'
]

LESSON_NAMES = [
    'Лекция: Основы', 'Семинар: Углублённое изучение', 'Практика: Отработка навыков',
    'Лабораторная: Эксперимент', 'Консультация', 'Зачёт', 'Экзамен',
    'Практическое занятие', 'Вождение: Город', 'Вождение: Автодром',
    'Вождение: Трасса', 'Теоретический курс', 'Мастер-класс', 'Деловая игра'
]

MEDICAL_CERTS = ['Справка 086/у', 'Справка 003-В/у', 'Действующая', 'Истекла', 'Отсутствует']
PASSPORT_PREFIXES = ['4500', '4501', '4502', '4503', '4504', '4505', '4506', '4507', '4508', '4509']

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


def generate_employees(count=50):
    """Generate employee records"""
    positions = list(range(1, 11))  # position_ids
    employees = []
    
    for i in range(1, count + 1):
        if i <= 20:
            name = FIRST_NAMES_MALE[i-1] if i % 3 != 0 else FIRST_NAMES_FEMALE[i-1]
        else:
            last_name = random.choice(LAST_NAMES)
            gender = random.choice(['male', 'female'])
            if gender == 'male':
                first = random.choice(['Алексей', 'Дмитрий', 'Сергей', 'Андрей', 'Николай', 'Павел', 'Максим', 'Юрий', 'Артём', 'Владимир'])
                name = f"{last_name} {first}"
            else:
                first = random.choice(['Мария', 'Анна', 'Елена', 'Ольга', 'Татьяна', 'Наталья', 'Ирина', 'Светлана', 'Юлия', 'Екатерина'])
                name = f"{last_name}а {first}"
        
        experience = random.randint(1, 30)
        email = generate_email(name)
        phone = generate_phone()
        position_id = random.choice(positions)
        
        employees.append((i, name, experience, email, phone, position_id))
    
    return employees


def generate_cadets(count=200):
    """Generate cadet records"""
    cadets = []
    
    for i in range(1, count + 1):
        last_name = random.choice(LAST_NAMES)
        gender = random.choice(['male', 'female'])
        if gender == 'male':
            first = random.choice(['Алексей', 'Дмитрий', 'Сергей', 'Андрей', 'Николай', 'Павел', 'Максим', 'Юрий', 'Артём', 'Владимир', 'Роман', 'Игорь', 'Тимур', 'Илья', 'Фёдор'])
            full_name = f"{last_name} {first}"
        else:
            first = random.choice(['Мария', 'Анна', 'Елена', 'Ольга', 'Татьяна', 'Наталья', 'Ирина', 'Светлана', 'Юлия', 'Екатерина', 'Алина', 'Ксения', 'Полина', 'Вера', 'Диана'])
            full_name = f"{last_name}а {first}"
        
        passport = generate_passport()
        med_cert = random.choice(MEDICAL_CERTS)
        age = random.randint(16, 35)
        group_id = random.randint(1, 10)  # group_ids 1-10
        
        cadets.append((i, passport, full_name, med_cert, age, group_id))
    
    return cadets


def generate_lessons(count=300, employee_ids=None):
    """Generate lesson records"""
    lessons = []
    employee_ids = employee_ids or list(range(1, 51))
    
    for i in range(1, count + 1):
        result = random.choice(['Зачтено', 'Не зачтено', 'Выполнено', 'В процессе', None, None])
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


def generate_cadet_lessons(cadet_ids, lesson_ids, avg_lessons_per_cadet=5):
    """Generate cadet-lesson associations"""
    associations = set()
    
    for cadet_id in cadet_ids:
        num_lessons = random.randint(2, avg_lessons_per_cadet + 2)
        selected_lessons = random.sample(lesson_ids, min(num_lessons, len(lesson_ids)))
        for lesson_id in selected_lessons:
            associations.add((cadet_id, lesson_id))
    
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


def generate_sql_inserts(output_file='database/populate_main_tables.sql'):
    """Generate SQL INSERT statements for all main tables"""
    
    random.seed(42)  # Reproducible results
    
    employees = generate_employees(50)
    cadets = generate_cadets(200)
    lessons = generate_lessons(300, employee_ids=list(range(1, 51)))
    
    cadet_ids = list(range(1, 201))
    lesson_ids = list(range(1, 301))
    group_ids = list(range(1, 11))
    
    cadet_lessons = generate_cadet_lessons(cadet_ids, lesson_ids)
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
    
    # Cadets
    sql_lines.append("-- ============================================================================")
    sql_lines.append("-- Cadets (Курсанты)")
    sql_lines.append("-- ============================================================================\n")
    sql_lines.append("INSERT INTO public.cadets (id, passport_number, full_name, medical_certificate, age, group_id) VALUES")
    
    cadet_values = []
    for cadet in cadets:
        cadet_values.append(f"({cadet[0]}, '{cadet[1]}', '{cadet[2]}', '{cadet[3]}', {cadet[4]}, {cadet[5]})")
    sql_lines.append(',\n'.join(cadet_values) + ';')
    sql_lines.append(f"\nSELECT setval('public.cadets_id_seq', (SELECT MAX(id) FROM public.cadets));\n")
    
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
    
    # Cadet-Lessons
    sql_lines.append("-- ============================================================================")
    sql_lines.append("-- Cadet-Lesson Associations (Курсант-Занятия)")
    sql_lines.append("-- ============================================================================\n")
    sql_lines.append("INSERT INTO public.cadet_lessons (cadet_id, lesson_id) VALUES")
    
    cl_values = []
    for cl in cadet_lessons:
        cl_values.append(f"({cl[0]}, {cl[1]})")
    sql_lines.append(',\n'.join(cl_values) + ';\n')
    
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
    sql_lines.append(f"-- Cadets: {len(cadets)}")
    sql_lines.append(f"-- Lessons: {len(lessons)}")
    sql_lines.append(f"-- Cadet-Lesson associations: {len(cadet_lessons)}")
    sql_lines.append(f"-- Group-Lesson associations: {len(group_lessons)}")
    sql_lines.append("-- ============================================================================\n")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))
    
    print(f"SQL file generated: {output_file}")
    print(f"  Employees: {len(employees)}")
    print(f"  Cadets: {len(cadets)}")
    print(f"  Lessons: {len(lessons)}")
    print(f"  Cadet-Lesson associations: {len(cadet_lessons)}")
    print(f"  Group-Lesson associations: {len(group_lessons)}")


if __name__ == '__main__':
    generate_sql_inserts()
