"""
Educational Process Management System - Desktop Application (PyQt6)
"""

import sys
import json
import os
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QComboBox, QSpinBox, QDateEdit, QTextEdit, QPlainTextEdit, QDialog, QFormLayout,
    QDialogButtonBox, QMessageBox, QHeaderView, QSplitter, QTreeWidget,
    QTreeWidgetItem, QStackedWidget, QToolBar, QStatusBar, QInputDialog,
    QFileDialog, QFrame, QGroupBox, QGridLayout, QTabWidget
)
from PyQt6.QtCore import Qt, QDate, QTime, QSize
from PyQt6.QtGui import QAction, QIcon, QFont, QColor, QPixmap
try:
    import pg8000
except ImportError as e:
    raise ImportError(
        "pg8000 is not installed for the active Python interpreter. "
        "Activate backend\\venv or use backend\\venv\\Scripts\\python.exe to run app.py."
    ) from e
from logging_config import setup_logging
from datetime import datetime

# Load configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

logger = setup_logging(__name__, 'app.log')


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.db_config = CONFIG['database']
        self.lookup_tables = CONFIG.get('lookup_tables', [])
    
    def get_connection(self):
        host = str(self.db_config['host'])
        port = int(self.db_config['port'])
        dbname = str(self.db_config['name'])
        user = str(self.db_config['user'])
        password = str(self.db_config['password'])

        logger.debug('Connecting to PostgreSQL host=%r port=%r dbname=%r user=%r', host, port, dbname, user)
        try:
            return pg8000.connect(
                host=host,
                port=port,
                database=dbname,
                user=user,
                password=password
            )
        except pg8000.dbapi.ProgrammingError as e:
            err = e.args[0] if e.args else None
            if isinstance(err, dict) and err.get('C') == '3D000':
                raise RuntimeError(
                    f"Database '{dbname}' does not exist. Run start.bat or database\\setup_database.bat to create it."
                ) from e
            raise
    
    def execute_query(self, query, params=None, fetch=True):
        conn = None
        logger.info('Executing query: %s params=%s', query, params)
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())

            if fetch:
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                result = [self._serialize_row(dict(zip(columns, row))) for row in rows]
                cursor.close()
                conn.close()
                return result
            else:
                conn.commit()
                cursor.close()
                conn.close()
                return True
        except Exception:
            if conn:
                conn.rollback()
                conn.close()
            logger.exception('Database error')
            raise
    
    def _serialize_row(self, row):
        serialized = {}
        for key, value in row.items():
            if hasattr(value, 'isoformat'):
                serialized[key] = value.isoformat()
            elif isinstance(value, bytes):
                try:
                    serialized[key] = value.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        serialized[key] = value.decode('cp1251')
                    except UnicodeDecodeError:
                        serialized[key] = value.decode('utf-8', errors='replace')
            elif isinstance(value, str):
                serialized[key] = value
            else:
                serialized[key] = value
        return serialized
    
    def get_all(self, table_name, filters=None):
        table_info = TABLES.get(table_name)
        if not table_info:
            raise ValueError(f"Unknown table: {table_name}")
        
        query = f"SELECT * FROM public.{table_info['table']}"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                if value and value.strip():
                    conditions.append(f"{key} ILIKE %s")
                    params.append(f"%{value}%")
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        pk = table_info['primary_key'] if isinstance(table_info['primary_key'], str) else table_info['primary_key'][0]
        query += f" ORDER BY {pk}"
        
        return self.execute_query(query, params if params else None)
    
    def get_by_id(self, table_name, record_id):
        table_info = TABLES.get(table_name)
        if not table_info:
            raise ValueError(f"Unknown table: {table_name}")
        
        if isinstance(table_info['primary_key'], tuple):
            keys = table_info['primary_key']
            conditions = " AND ".join([f"{key} = %s" for key in keys])
            query = f"SELECT * FROM public.{table_info['table']} WHERE {conditions}"
            result = self.execute_query(query, record_id)
        else:
            query = f"SELECT * FROM public.{table_info['table']} WHERE {table_info['primary_key']} = %s"
            result = self.execute_query(query, [record_id])
        
        return result[0] if result else None
    
    def create(self, table_name, data):
        table_info = TABLES.get(table_name)
        if not table_info:
            raise ValueError(f"Unknown table: {table_name}")
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO public.{table_info['table']} ({columns}) VALUES ({placeholders}) RETURNING *"
        
        result = self.execute_query(query, list(data.values()))
        return result[0] if result else None
    
    def update(self, table_name, record_id, data):
        table_info = TABLES.get(table_name)
        if not table_info:
            raise ValueError(f"Unknown table: {table_name}")
        
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        
        if isinstance(table_info['primary_key'], tuple):
            keys = table_info['primary_key']
            conditions = " AND ".join([f"{key} = %s" for key in keys])
            query = f"UPDATE public.{table_info['table']} SET {set_clause} WHERE {conditions} RETURNING *"
            params = list(data.values()) + list(record_id)
        else:
            query = f"UPDATE public.{table_info['table']} SET {set_clause} WHERE {table_info['primary_key']} = %s RETURNING *"
            params = list(data.values()) + [record_id]
        
        result = self.execute_query(query, params)
        return result[0] if result else None
    
    def delete(self, table_name, record_id):
        table_info = TABLES.get(table_name)
        if not table_info:
            raise ValueError(f"Unknown table: {table_name}")
        
        if isinstance(table_info['primary_key'], tuple):
            keys = table_info['primary_key']
            conditions = " AND ".join([f"{key} = %s" for key in keys])
            query = f"DELETE FROM public.{table_info['table']} WHERE {conditions} RETURNING *"
            params = list(record_id)
        else:
            query = f"DELETE FROM public.{table_info['table']} WHERE {table_info['primary_key']} = %s RETURNING *"
            params = [record_id]
        
        result = self.execute_query(query, params)
        return result[0] if result else None
    
    def get_statistics(self):
        stats = {}
        for table_name, table_info in TABLES.items():
            count = self.execute_query(f"SELECT COUNT(*) as count FROM public.{table_info['table']}")
            stats[table_name] = count[0]['count'] if count else 0
        return stats
    
    def get_reference_data(self, table_name, label_field):
        """Get data for dropdown (foreign key references)"""
        try:
            result = self.execute_query(f"SELECT id, {label_field} as label FROM public.{table_name} ORDER BY id")
            return [(row['id'], row['label']) for row in result]
        except:
            return []
    
    def create_backup(self):
        """Create database backup using pg_dump"""
        import subprocess
        
        backup_dir = os.path.join(os.path.dirname(__file__), '..', 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f"educational_process_{timestamp}.sql")
        
        try:
            db = self.db_config
            pg_bin = os.environ.get('PG_BIN', r'C:\Program Files\PostgreSQL\16\bin')
            pg_dump = os.path.join(pg_bin, 'pg_dump.exe')
            
            env = os.environ.copy()
            env['PGPASSWORD'] = db['password']
            
            cmd = [
                pg_dump,
                '-U', db['user'],
                '-h', db['host'],
                '-p', str(db['port']),
                '-d', db['name'],
                '-F', 'p',
                '-f', backup_file
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {'status': 'success', 'file': backup_file}
            else:
                return {'status': 'error', 'message': result.stderr}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


# Table configurations
TABLES = {
    'employees': {
        'table': 'employees',
        'primary_key': 'id',
        'lookup': False,
        'title': 'Сотрудники',
        'icon': '👨‍🏫',
        'columns': [
            {'key': 'id', 'label': 'ID', 'type': 'number', 'readonly': True},
            {'key': 'name', 'label': 'ФИО', 'type': 'text'},
            {'key': 'experience', 'label': 'Стаж (лет)', 'type': 'number'},
            {'key': 'email', 'label': 'Эл.почта', 'type': 'email'},
            {'key': 'phone', 'label': '№ телефона', 'type': 'text'},
            {'key': 'position_id', 'label': 'Должность', 'type': 'reference', 'ref_table': 'positions', 'ref_label': 'name'}
        ]
    },
    'students': {
        'table': 'students',
        'primary_key': 'id',
        'lookup': False,
        'title': 'Ученики',
        'icon': '👨‍🎓',
        'columns': [
            {'key': 'id', 'label': 'ID', 'type': 'number', 'readonly': True},
            {'key': 'passport_number', 'label': '№ паспорта', 'type': 'text'},
            {'key': 'full_name', 'label': 'ФИО', 'type': 'text'},
            {'key': 'medical_certificate', 'label': 'Мед.справка', 'type': 'text'},
            {'key': 'age', 'label': 'Возраст', 'type': 'number'},
            {'key': 'group_id', 'label': 'Группа', 'type': 'reference', 'ref_table': 'groups', 'ref_label': 'group_number'}
        ]
    },
    'lessons': {
        'table': 'lessons',
        'primary_key': 'id',
        'lookup': False,
        'title': 'Занятия',
        'icon': '🚗',
        'columns': [
            {'key': 'id', 'label': 'ID', 'type': 'number', 'readonly': True},
            {'key': 'name', 'label': 'Название', 'type': 'text'},
            {'key': 'topic', 'label': 'Тема', 'type': 'text'},
            {'key': 'lesson_date', 'label': 'Дата', 'type': 'date'},
            {'key': 'lesson_time', 'label': 'Время', 'type': 'time'},
            {'key': 'result', 'label': 'Результат', 'type': 'text'},
            {'key': 'contact_email', 'label': 'Эл.почта', 'type': 'email'},
            {'key': 'location_id', 'label': 'Место', 'type': 'reference', 'ref_table': 'locations', 'ref_label': 'address'},
            {'key': 'vehicle_id', 'label': 'Автомобиль', 'type': 'reference', 'ref_table': 'vehicles', 'ref_label': 'vehicle_number'},
            {'key': 'format_id', 'label': 'Формат', 'type': 'reference', 'ref_table': 'lesson_formats', 'ref_label': 'name'},
            {'key': 'employee_id', 'label': 'Инструктор', 'type': 'reference', 'ref_table': 'employees', 'ref_label': 'name'}
        ]
    },
    'groups': {
        'table': 'groups',
        'primary_key': 'id',
        'lookup': True,
        'title': 'Группы',
        'icon': '👥',
        'columns': [
            {'key': 'id', 'label': 'ID', 'type': 'number', 'readonly': True},
            {'key': 'group_number', 'label': '№ группы', 'type': 'text'},
            {'key': 'room_number', 'label': 'Аудитория', 'type': 'text'},
            {'key': 'format_type', 'label': 'Формат обучения', 'type': 'text'}
        ]
    },
    'positions': {
        'table': 'positions',
        'primary_key': 'id',
        'lookup': True,
        'title': 'Должности',
        'icon': '💼',
        'columns': [
            {'key': 'id', 'label': 'ID', 'type': 'number', 'readonly': True},
            {'key': 'name', 'label': 'Название', 'type': 'text'},
            {'key': 'phone', 'label': '№ телефона', 'type': 'text'},
            {'key': 'employment_type', 'label': 'Тип занятости', 'type': 'text'},
            {'key': 'notes', 'label': 'Замечания', 'type': 'textarea'}
        ]
    },
    'locations': {
        'table': 'locations',
        'primary_key': 'id',
        'lookup': True,
        'title': 'Места проведения',
        'icon': '📍',
        'columns': [
            {'key': 'id', 'label': 'ID', 'type': 'number', 'readonly': True},
            {'key': 'geolocation', 'label': 'Геолокация', 'type': 'text'},
            {'key': 'location_type', 'label': 'Тип помещения', 'type': 'text'},
            {'key': 'address', 'label': 'Адрес', 'type': 'text'},
            {'key': 'responsible_employee_id', 'label': 'Ответственный', 'type': 'reference', 'ref_table': 'employees', 'ref_label': 'name'}
        ]
    },
    'vehicles': {
        'table': 'vehicles',
        'primary_key': 'id',
        'lookup': True,
        'title': 'Автомобили',
        'icon': '🚗',
        'columns': [
            {'key': 'id', 'label': 'ID', 'type': 'number', 'readonly': True},
            {'key': 'vehicle_number', 'label': '№ автомобиля', 'type': 'text'},
            {'key': 'route', 'label': 'Маршрут', 'type': 'text'},
            {'key': 'notes', 'label': 'Замечания', 'type': 'textarea'},
            {'key': 'category', 'label': 'Категория', 'type': 'text'}
        ]
    },
    'lesson-formats': {
        'table': 'lesson_formats',
        'primary_key': 'id',
        'lookup': True,
        'title': 'Формы обучения',
        'icon': '📋',
        'columns': [
            {'key': 'id', 'label': 'ID', 'type': 'number', 'readonly': True},
            {'key': 'name', 'label': 'Название', 'type': 'text'}
        ]
    }
}

SPECIAL_QUERIES = [
    {'name': 'Все сотрудники (первые 50)', 'sql': 'SELECT id, name, experience, email, phone, position_id FROM public.employees ORDER BY id LIMIT 50;'},
    {'name': 'Все ученики (первые 50)', 'sql': 'SELECT id, passport_number, full_name, medical_certificate, age, group_id FROM public.students ORDER BY id LIMIT 50;'},
    {'name': 'Все занятия (первые 50)', 'sql': 'SELECT id, name, topic, lesson_date, lesson_time, result, contact_email FROM public.lessons ORDER BY lesson_date DESC, lesson_time DESC LIMIT 50;'},
    {'name': 'Список групп', 'sql': 'SELECT id, group_number, room_number, format_type FROM public.groups ORDER BY id;'},
    {'name': 'Список должностей', 'sql': 'SELECT id, name, phone, employment_type, notes FROM public.positions ORDER BY id;'},
    {'name': 'Список мест проведения', 'sql': 'SELECT id, geolocation, location_type, address, responsible_employee_id FROM public.locations ORDER BY id;'},
    {'name': 'Список автомобилей', 'sql': 'SELECT id, vehicle_number, route, notes, category FROM public.vehicles ORDER BY id;'},
    {'name': 'Список форм обучения', 'sql': 'SELECT id, name FROM public.lesson_formats ORDER BY id;'},
    {'name': 'Количество сотрудников', 'sql': 'SELECT COUNT(*) AS employee_count FROM public.employees;'},
    {'name': 'Количество учеников', 'sql': 'SELECT COUNT(*) AS student_count FROM public.students;'},
    {'name': 'Количество занятий', 'sql': 'SELECT COUNT(*) AS lesson_count FROM public.lessons;'},
    {'name': 'Количество групп по формату', 'sql': 'SELECT format_type, COUNT(*) AS group_count FROM public.groups GROUP BY format_type ORDER BY group_count DESC;'},
    {'name': 'Количество уроков по формату', 'sql': 'SELECT lf.name AS format_name, COUNT(*) AS lessons_count FROM public.lessons l JOIN public.lesson_formats lf ON l.format_id = lf.id GROUP BY lf.name ORDER BY lessons_count DESC;'},
    {'name': 'Количество уроков по локациям', 'sql': 'SELECT location_id, COUNT(*) AS lessons_count FROM public.lessons GROUP BY location_id ORDER BY lessons_count DESC;'},
    {'name': 'Сотрудники по стажу', 'sql': 'SELECT id, name, experience, position_id FROM public.employees ORDER BY experience DESC LIMIT 50;'},
    {'name': 'Ученики по возрасту', 'sql': 'SELECT id, full_name, age, group_id FROM public.students ORDER BY age DESC LIMIT 50;'},
    {'name': 'Занятия без автомобиля', 'sql': 'SELECT id, name, topic, lesson_date, lesson_time, employee_id FROM public.lessons WHERE vehicle_id IS NULL ORDER BY lesson_date DESC LIMIT 50;'},
    {'name': 'Занятия с результатом «Не зачтено»', 'sql': 'SELECT id, name, topic, lesson_date, lesson_time, result FROM public.lessons WHERE result ILIKE ''%Не зачтено%'' ORDER BY lesson_date DESC LIMIT 50;'},
    {'name': 'Занятия c датой в ближайшие 30 дней', 'sql': 'SELECT id, name, topic, lesson_date, lesson_time FROM public.lessons WHERE lesson_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL ''30 days'' ORDER BY lesson_date, lesson_time;'},
    {'name': 'Ученики 18-25 лет', 'sql': 'SELECT id, full_name, age, group_id FROM public.students WHERE age BETWEEN 18 AND 25 ORDER BY age, full_name;'},
    {'name': 'Группы в аудитории 101', 'sql': 'SELECT id, group_number, room_number, format_type FROM public.groups WHERE room_number = ''101'';'},
    {'name': 'Автомобили категории B', 'sql': 'SELECT id, vehicle_number, route, notes FROM public.vehicles WHERE category = ''B'' ORDER BY vehicle_number;'},
    {'name': 'Места типа «Аудитория»', 'sql': 'SELECT id, address, location_type, responsible_employee_id FROM public.locations WHERE location_type ILIKE ''%Аудитория%'' ORDER BY id;'},
    {'name': 'Сотрудники с email на gmail', 'sql': 'SELECT id, name, email, phone FROM public.employees WHERE email ILIKE ''%gmail.com'' ORDER BY name;'},
    {'name': 'Студенты с медсправкой отсутствует', 'sql': 'SELECT id, full_name, medical_certificate, age FROM public.students WHERE medical_certificate ILIKE ''%Отсутствует%'' ORDER BY full_name;'},
    {'name': 'Связь сотрудников и должностей', 'sql': 'SELECT e.id, e.name AS employee, p.name AS position FROM public.employees e JOIN public.positions p ON e.position_id = p.id ORDER BY e.name LIMIT 50;'},
    {'name': 'Занятия с форматами обучения', 'sql': 'SELECT l.id, l.name, lf.name AS format_name, l.lesson_date, l.lesson_time FROM public.lessons l JOIN public.lesson_formats lf ON l.format_id = lf.id ORDER BY l.lesson_date DESC LIMIT 50;'},
    {'name': 'Занятия с адресами локаций', 'sql': 'SELECT l.id, l.name, loc.address, l.lesson_date, l.lesson_time FROM public.lessons l JOIN public.locations loc ON l.location_id = loc.id ORDER BY l.lesson_date DESC LIMIT 50;'},
    {'name': 'Занятия с инструкторами', 'sql': 'SELECT l.id, l.name, e.name AS instructor, l.lesson_date, l.lesson_time FROM public.lessons l JOIN public.employees e ON l.employee_id = e.id ORDER BY l.lesson_date DESC LIMIT 50;'},
    {'name': 'Ученики по группам', 'sql': 'SELECT s.id, s.full_name, g.group_number FROM public.students s JOIN public.groups g ON s.group_id = g.id ORDER BY g.group_number, s.full_name LIMIT 50;'},
    {'name': 'Количество учеников в каждой группе', 'sql': 'SELECT g.group_number, COUNT(s.id) AS student_count FROM public.groups g LEFT JOIN public.students s ON s.group_id = g.id GROUP BY g.group_number ORDER BY student_count DESC;'},
    {'name': 'Количество уроков на каждого инструктора', 'sql': 'SELECT e.name AS instructor, COUNT(l.id) AS lessons_count FROM public.employees e LEFT JOIN public.lessons l ON l.employee_id = e.id GROUP BY e.name ORDER BY lessons_count DESC LIMIT 50;'},
    {'name': 'Список маршрутов автомобилей', 'sql': 'SELECT id, vehicle_number, route, category FROM public.vehicles ORDER BY id;'},
    {'name': 'Отличающиеся результаты уроков', 'sql': 'SELECT DISTINCT result FROM public.lessons ORDER BY result;'},
    {'name': 'Группы со смешанным форматом', 'sql': 'SELECT id, group_number, room_number, format_type FROM public.groups WHERE format_type ILIKE ''%Смешанно%'';'},
    {'name': 'Адреса онлайн-платформ', 'sql': 'SELECT id, address, location_type FROM public.locations WHERE address ILIKE ''%Zoom%'' OR address ILIKE ''%Moodle%'';'},
    {'name': 'Автомобили с заметками', 'sql': "SELECT id, vehicle_number, route, notes FROM public.vehicles WHERE notes IS NOT NULL AND notes <> '' ORDER BY id;"},
    {'name': 'Сотрудники с наибольшим стажем', 'sql': 'SELECT id, name, experience FROM public.employees ORDER BY experience DESC LIMIT 25;'},
    {'name': 'Последние 50 записей по дате занятия', 'sql': 'SELECT id, name, lesson_date, lesson_time, result FROM public.lessons ORDER BY lesson_date DESC, lesson_time DESC LIMIT 50;'},
    {'name': 'Уроки без результата', 'sql': 'SELECT id, name, topic, lesson_date, lesson_time FROM public.lessons WHERE result IS NULL ORDER BY lesson_date DESC LIMIT 50;'},
    {'name': 'Студенты с паспортом по группе', 'sql': 'SELECT id, full_name, passport_number, group_id FROM public.students ORDER BY group_id, full_name LIMIT 50;'},
    {'name': 'Сотрудники, не являющиеся инструкторами', 'sql': 'SELECT id, name, position_id FROM public.employees WHERE position_id <> 9 ORDER BY name LIMIT 50;'},
    {'name': 'Группы по номеру аудитории', 'sql': 'SELECT group_number, room_number, format_type FROM public.groups ORDER BY room_number, group_number;'},
    {'name': 'Форматы обучения и количество уроков', 'sql': 'SELECT lf.name AS format_name, COUNT(l.id) AS lessons_count FROM public.lesson_formats lf LEFT JOIN public.lessons l ON l.format_id = lf.id GROUP BY lf.name ORDER BY lessons_count DESC;'},
    {'name': 'Локации и ответственные сотрудники', 'sql': 'SELECT loc.address, loc.location_type, e.name AS responsible FROM public.locations loc LEFT JOIN public.employees e ON loc.responsible_employee_id = e.id ORDER BY loc.address LIMIT 50;'},
    {'name': 'Автомобили по категориям и маршрутам', 'sql': 'SELECT category, vehicle_number, route FROM public.vehicles ORDER BY category, vehicle_number;'},
    {'name': 'Все уроки с датой и временем', 'sql': 'SELECT id, name, lesson_date, lesson_time, result FROM public.lessons ORDER BY lesson_date, lesson_time LIMIT 100;'},
    {'name': 'Список всех email сотрудников', 'sql': 'SELECT id, name, email FROM public.employees WHERE email IS NOT NULL ORDER BY name LIMIT 100;'},
    {'name': 'Студенты по номеру паспорта', 'sql': 'SELECT id, full_name, passport_number FROM public.students ORDER BY passport_number LIMIT 100;'},
    {'name': 'Сотрудники с телефонным номером', 'sql': 'SELECT id, name, phone FROM public.employees WHERE phone IS NOT NULL ORDER BY name;'},
    {'name': 'Занятия по теме и месту', 'sql': 'SELECT l.id, l.topic, loc.address, l.lesson_date FROM public.lessons l JOIN public.locations loc ON l.location_id = loc.id ORDER BY l.lesson_date DESC LIMIT 50;'},
    {'name': 'Группы, имеющие формат «Дистанционно»', 'sql': 'SELECT id, group_number, room_number, format_type FROM public.groups WHERE format_type ILIKE ''%Дистанционно%'';'},
    {'name': 'Ученики старше 25 лет', 'sql': 'SELECT id, full_name, age, group_id FROM public.students WHERE age > 25 ORDER BY age DESC LIMIT 50;'},
    {'name': 'Все заметки по позициям', 'sql': 'SELECT id, name, employment_type, notes FROM public.positions WHERE notes IS NOT NULL ORDER BY id;'},
    {'name': 'Подробный список уроков с форматом и инструктором', 'sql': 'SELECT l.id, l.name, lf.name AS format_name, e.name AS instructor, l.lesson_date, l.lesson_time FROM public.lessons l JOIN public.lesson_formats lf ON l.format_id = lf.id JOIN public.employees e ON l.employee_id = e.id ORDER BY l.lesson_date DESC LIMIT 50;'},
    {'name': 'Пять уроков с ближайшей датой', 'sql': 'SELECT id, name, lesson_date, lesson_time FROM public.lessons WHERE lesson_date >= CURRENT_DATE ORDER BY lesson_date, lesson_time LIMIT 5;'},
    {'name': 'Количество учеников по каждой группе', 'sql': 'SELECT g.group_number, COUNT(s.id) AS student_count FROM public.groups g LEFT JOIN public.students s ON s.group_id = g.id GROUP BY g.group_number ORDER BY g.group_number;'},
    {'name': 'Список всех адресов локаций', 'sql': 'SELECT id, address FROM public.locations ORDER BY id;'},
    {'name': 'Прочитать только первые 20 строк из lessons', 'sql': 'SELECT * FROM public.lessons ORDER BY id LIMIT 20;'},
    {'name': 'Список всех уникальных категорий автомобилей', 'sql': 'SELECT DISTINCT category FROM public.vehicles ORDER BY category;'},
    {'name': 'Поиск студентов по группе 1', 'sql': 'SELECT id, full_name, age FROM public.students WHERE group_id = 1 ORDER BY full_name;'},
]


class RecordDialog(QDialog):
    """Dialog for adding/editing records"""
    
    def __init__(self, table_name, parent=None, edit_mode=False, record=None):
        super().__init__(parent)
        self.table_name = table_name
        self.edit_mode = edit_mode
        self.record = record
        self.db = DatabaseManager()

        self.setWindowTitle(f"{'Редактировать' if edit_mode else 'Добавить'} — {TABLES[table_name]['title']}")
        self.setMinimumWidth(550)
        self.setMinimumHeight(400)

        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        config = TABLES[self.table_name]
        self.fields = {}

        for col in config['columns']:
            if col['readonly'] and self.edit_mode:
                # Show readonly fields as labels
                value = str(self.record.get(col['key'], '')) if self.record else ''
                label = QLabel(value)
                label.setFont(QFont("Segoe UI", 11))
                label.setStyleSheet("""
                    padding: 8px 12px;
                    background: #334155;
                    border: 1px solid #475569;
                    border-radius: 6px;
                    color: #94a3b8;
                """)
                form_layout.addRow(col['label'] + ":", label)
            elif col['readonly'] and not self.edit_mode:
                continue
            else:
                widget = self.create_widget(col)
                if self.edit_mode and self.record:
                    self.set_widget_value(widget, col, self.record.get(col['key']))

                form_layout.addRow(col['label'] + ":", widget)
                self.fields[col['key']] = (widget, col)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumHeight(42)
        cancel_btn.setFont(QFont("Segoe UI", 12))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #475569;
                color: #f1f5f9;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: #64748b;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Сохранить")
        save_btn.setMinimumHeight(42)
        save_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)
    
    def create_widget(self, col):
        if col['type'] == 'reference':
            combo = QComboBox()
            combo.setMinimumHeight(38)
            combo.setFont(QFont("Segoe UI", 11))
            combo.setCursor(Qt.CursorShape.PointingHandCursor)
            combo.addItem('-- Выберите --', userData=None)
            ref_data = self.db.get_reference_data(col['ref_table'], col['ref_label'])
            for ref_id, ref_label in ref_data:
                combo.addItem(str(ref_label), userData=ref_id)
            return combo
        elif col['type'] == 'number':
            spin = QSpinBox()
            spin.setRange(-99999, 999999)
            spin.setMinimumHeight(38)
            spin.setFont(QFont("Segoe UI", 11))
            return spin
        elif col['type'] == 'date':
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_edit.setDate(QDate.currentDate())
            date_edit.setMinimumHeight(38)
            date_edit.setFont(QFont("Segoe UI", 11))
            date_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            return date_edit
        elif col['type'] == 'time':
            time_edit = QDateEdit()
            time_edit.setTime(QTime.currentTime())
            time_edit.setMinimumHeight(38)
            time_edit.setFont(QFont("Segoe UI", 11))
            time_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            return time_edit
        elif col['type'] == 'textarea':
            text_edit = QTextEdit()
            text_edit.setMaximumHeight(80)
            text_edit.setFont(QFont("Segoe UI", 11))
            return text_edit
        else:
            line_edit = QLineEdit()
            line_edit.setMinimumHeight(38)
            line_edit.setFont(QFont("Segoe UI", 11))
            return line_edit
    
    def set_widget_value(self, widget, col, value):
        if col['type'] == 'reference':
            if value:
                for i in range(widget.count()):
                    if widget.itemData(i) == value:
                        widget.setCurrentIndex(i)
                        break
        elif col['type'] == 'number':
            widget.setValue(value if value else 0)
        elif col['type'] == 'date' and value:
            try:
                date = QDate.fromString(str(value)[:10], 'yyyy-MM-dd')
                widget.setDate(date)
            except:
                pass
        elif col['type'] == 'time' and value:
            try:
                time_parts = str(value).split(':')
                if len(time_parts) >= 2:
                    widget.setTime(QTime(int(time_parts[0]), int(time_parts[1])))
            except:
                pass
        elif col['type'] == 'textarea':
            widget.setPlainText(value if value else '')
        else:
            widget.setText(str(value) if value else '')
    
    def get_values(self):
        data = {}
        for key, (widget, col) in self.fields.items():
            if col['readonly']:
                continue
            
            if col['type'] == 'reference':
                data[key] = widget.currentData()
            elif col['type'] == 'number':
                data[key] = widget.value()
            elif col['type'] == 'date':
                data[key] = widget.date().toString('yyyy-MM-dd')
            elif col['type'] == 'time':
                data[key] = widget.time().toString('hh:mm:ss')
            elif col['type'] == 'textarea':
                data[key] = widget.toPlainText()
            else:
                data[key] = widget.text()
            
            # Remove None values (keep null fields as None)
            if data[key] == '' or data[key] is None:
                data[key] = None
        
        return data


class DataTableWidget(QWidget):
    """Table view with CRUD operations"""
    
    def __init__(self, table_name, parent=None):
        super().__init__(parent)
        self.table_name = table_name
        self.db = DatabaseManager()
        self.current_data = []
        self.main_window = parent
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍  Поиск...")
        self.search_edit.setMinimumHeight(40)
        self.search_edit.setFont(QFont("Segoe UI", 11))
        self.search_edit.textChanged.connect(self.filter_data)
        toolbar.addWidget(self.search_edit)

        btn_add = QPushButton("➕  Добавить")
        btn_add.setMinimumHeight(40)
        btn_add.setFont(QFont("Segoe UI", 11))
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self.add_record)
        toolbar.addWidget(btn_add)

        btn_refresh = QPushButton("🔄  Обновить")
        btn_refresh.setMinimumHeight(40)
        btn_refresh.setFont(QFont("Segoe UI", 11))
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.clicked.connect(self.load_data)
        toolbar.addWidget(btn_refresh)

        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(400)
        self.table.setFont(QFont("Segoe UI", 11))

        # Double-click to edit
        self.table.cellDoubleClicked.connect(lambda row, col: self.edit_record())

        layout.addWidget(self.table)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        btn_edit = QPushButton("✏️  Редактировать")
        btn_edit.setMinimumHeight(40)
        btn_edit.setFont(QFont("Segoe UI", 11))
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.clicked.connect(self.edit_record)
        button_layout.addWidget(btn_edit)

        btn_delete = QPushButton("🗑️  Удалить")
        btn_delete.setMinimumHeight(40)
        btn_delete.setFont(QFont("Segoe UI", 11))
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.clicked.connect(self.delete_record)
        button_layout.addWidget(btn_delete)

        layout.addLayout(button_layout)
    
    def load_data(self, filters=None):
        try:
            logger.info('Loading data for table %s filters=%s', self.table_name, filters)
            self.current_data = self.db.get_all(self.table_name, filters)
            self.populate_table()
        except Exception as e:
            logger.exception('Failed to load data for table %s', self.table_name)
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные:\n{str(e)}")
    
    def populate_table(self):
        config = TABLES[self.table_name]
        
        # Set headers
        self.table.setColumnCount(len(config['columns']))
        self.table.setHorizontalHeaderLabels([col['label'] for col in config['columns']])
        
        # Set rows
        self.table.setRowCount(len(self.current_data))
        
        for row_idx, record in enumerate(self.current_data):
            for col_idx, col in enumerate(config['columns']):
                value = record.get(col['key'])
                
                # Format value
                if value is None:
                    display_value = "-"
                elif col['type'] == 'reference':
                    # Show reference label instead of ID
                    display_value = self.get_reference_label(col, value)
                elif col['type'] == 'date' and value:
                    display_value = str(value)[:10]
                elif col['type'] == 'time' and value:
                    display_value = str(value)[:5]
                else:
                    display_value = str(value)
                
                item = QTableWidgetItem(display_value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)
    
    def get_reference_label(self, col, value):
        """Get display label for foreign key reference"""
        try:
            if col['type'] == 'reference':
                ref_data = self.db.get_reference_data(col['ref_table'], col['ref_label'])
                for ref_id, ref_label in ref_data:
                    if ref_id == value:
                        return str(ref_label)
        except:
            pass
        return str(value)
    
    def filter_data(self, text):
        if not text:
            self.load_data()
            return
        
        filters = {}
        config = TABLES[self.table_name]
        for col in config['columns']:
            if col['type'] in ['text', 'email']:
                filters[col['key']] = text
        
        self.load_data(filters)
    
    def get_selected_record(self):
        row = self.table.currentRow()
        if row >= 0 and row < len(self.current_data):
            return self.current_data[row]
        return None
    
    def add_record(self):
        # Check if lookup table requires superuser
        config = TABLES[self.table_name]
        if config['lookup'] and not self.main_window.is_superuser:
            reply = QMessageBox.question(
                self, "Требуется авторизация",
                "Для редактирования справочников требуется войти как суперпользователь.\nВойти сейчас?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.main_window.authenticate()
            return
        
        dialog = RecordDialog(self.table_name, self, edit_mode=False)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_values()
                logger.info('Creating record in %s: %s', self.table_name, data)
                self.db.create(self.table_name, data)
                QMessageBox.information(self, "Успех", "Запись успешно добавлена")
                self.load_data()
            except Exception as e:
                logger.exception('Failed to add record to %s', self.table_name)
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись:\n{str(e)}")
    
    def edit_record(self):
        record = self.get_selected_record()
        if not record:
            QMessageBox.warning(self, "Предупреждение", "Выберите запись для редактирования")
            return
        
        config = TABLES[self.table_name]
        if config['lookup'] and not self.main_window.is_superuser:
            QMessageBox.warning(self, "Требуется авторизация", "Для редактирования справочников требуется войти как суперпользователь")
            return
        
        dialog = RecordDialog(self.table_name, self, edit_mode=True, record=record)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_values()
                pk = config['primary_key']
                record_id = record[pk] if isinstance(pk, str) else record[pk[0]]
                logger.info('Updating record %s in %s: %s', record_id, self.table_name, data)
                self.db.update(self.table_name, record_id, data)
                QMessageBox.information(self, "Успех", "Запись успешно обновлена")
                self.load_data()
            except Exception as e:
                logger.exception('Failed to update record %s in %s', record_id, self.table_name)
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить запись:\n{str(e)}")
    
    def delete_record(self):
        record = self.get_selected_record()
        if not record:
            QMessageBox.warning(self, "Предупреждение", "Выберите запись для удаления")
            return
        
        config = TABLES[self.table_name]
        if config['lookup'] and not self.main_window.is_superuser:
            QMessageBox.warning(self, "Требуется авторизация", "Для удаления из справочников требуется войти как суперпользователь")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите удалить эту запись?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                pk = config['primary_key']
                record_id = record[pk] if isinstance(pk, str) else record[pk[0]]
                logger.info('Deleting record %s from %s', record_id, self.table_name)
                self.db.delete(self.table_name, record_id)
                QMessageBox.information(self, "Успех", "Запись успешно удалена")
                self.load_data()
            except Exception as e:
                logger.exception('Failed to delete record %s from %s', record_id, self.table_name)
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить запись:\n{str(e)}")


class DashboardWidget(QWidget):
    """Dashboard with statistics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.setup_ui()
        self.load_stats()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Title
        title = QLabel("📊 Панель управления")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("""
            color: #f1f5f9;
            padding: 10px 0;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Stats grid
        self.stats_layout = QGridLayout()
        self.stats_layout.setSpacing(12)
        layout.addLayout(self.stats_layout)

        # Welcome message
        welcome = QGroupBox("  Добро пожаловать в систему управления автошколой!")
        welcome.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        welcome.setStyleSheet("""
            QGroupBox {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 20px;
                margin-top: 16px;
                color: #f1f5f9;
            }
        """)
        welcome_layout = QVBoxLayout(welcome)

        info_label = QLabel(
            "Выберите раздел в боковом меню для начала работы.\n\n"
            "✅  Управление сотрудниками и учениками\n"
            "✅  Расписание занятий по вождению\n"
            "✅  Группы и места проведения\n"
            "✅  Создание резервных копий\n"
            "✅  Фильтрация и поиск данных"
        )
        info_label.setWordWrap(True)
        info_label.setFont(QFont("Segoe UI", 12))
        info_label.setStyleSheet("""
            color: #cbd5e1;
            padding: 8px;
            line-height: 1.6;
        """)
        welcome_layout.addWidget(info_label)

        layout.addWidget(welcome)
    
    def load_stats(self):
        try:
            stats = self.db.get_statistics()
            
            # Clear old stats
            for i in reversed(range(self.stats_layout.count())):
                self.stats_layout.itemAt(i).widget().setParent(None)
            
            # Create stat cards
            stat_cards = [
                ('👨‍🏫', 'Сотрудники', stats.get('employees', 0)),
                ('👨‍🎓', 'Ученики', stats.get('students', 0)),
                ('🚗', 'Занятия', stats.get('lessons', 0)),
                ('👥', 'Группы', stats.get('groups', 0)),
                ('💼', 'Должности', stats.get('positions', 0)),
                ('📍', 'Места', stats.get('locations', 0)),
                ('🚗', 'Автомобили', stats.get('vehicles', 0)),
                ('📋', 'Форматы', stats.get('lesson-formats', 0)),
            ]
            
            row = 0
            col = 0
            for icon, label, count in stat_cards:
                card = self.create_stat_card(icon, label, count)
                self.stats_layout.addWidget(card, row, col)
                col += 1
                if col >= 4:
                    col = 0
                    row += 1
        except Exception as e:
            logger.exception('Failed to load statistics')
    
    def create_stat_card(self, icon, label, count):
        card = QGroupBox()
        card.setStyleSheet("""
            QGroupBox {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 20px;
                margin: 4px;
            }
            QGroupBox:hover {
                border-color: #3b82f6;
                background: #1e293b;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(6)

        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 36))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        count_label = QLabel(str(count))
        count_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        count_label.setStyleSheet("color: #3b82f6;")
        count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(count_label)

        name_label = QLabel(label)
        name_label.setStyleSheet("color: #94a3b8; font-size: 13px;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        return card


class SqlQueryWidget(QWidget):
    """Page for executing custom SQL and prepared queries"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.main_window = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("🧪 SQL-запросы")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet("color: #f1f5f9; padding: 8px 0;")
        layout.addWidget(title)

        info = QLabel(
            "Выберите один из готовых запросов или введите свой SQL-запрос ниже, затем нажмите \"Выполнить\"."
        )
        info.setWordWrap(True)
        info.setFont(QFont("Segoe UI", 12))
        info.setStyleSheet("color: #94a3b8; padding: 8px;")
        layout.addWidget(info)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        self.query_combo = QComboBox()
        self.query_combo.setMinimumHeight(40)
        self.query_combo.setFont(QFont("Segoe UI", 11))
        for query in SPECIAL_QUERIES:
            self.query_combo.addItem(query['name'])
        self.query_combo.currentIndexChanged.connect(self.load_selected_query)
        control_layout.addWidget(self.query_combo)

        btn_load = QPushButton("Загрузить запрос")
        btn_load.setMinimumHeight(40)
        btn_load.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_load.clicked.connect(self.load_selected_query)
        control_layout.addWidget(btn_load)

        btn_run = QPushButton("Выполнить запрос")
        btn_run.setMinimumHeight(40)
        btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_run.clicked.connect(self.execute_current_query)
        control_layout.addWidget(btn_run)

        btn_clear = QPushButton("Очистить")
        btn_clear.setMinimumHeight(40)
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.clicked.connect(self.clear_query)
        control_layout.addWidget(btn_clear)

        layout.addLayout(control_layout)

        self.query_editor = QPlainTextEdit()
        self.query_editor.setPlaceholderText("Введите SQL-запрос здесь...")
        self.query_editor.setMinimumHeight(220)
        self.query_editor.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.query_editor)

        result_label = QLabel("Результаты запроса")
        result_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        result_label.setStyleSheet("color: #f1f5f9; padding: 8px 0;")
        layout.addWidget(result_label)

        self.result_table = QTableWidget()
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.result_table.setMinimumHeight(280)
        self.result_table.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.result_table)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setStyleSheet("padding: 12px; background: #1e293b; border-radius: 8px; border: 1px solid #334155; color: #94a3b8;")
        layout.addWidget(self.status_label)

        layout.addStretch()
        self.load_selected_query()

    def load_selected_query(self):
        idx = self.query_combo.currentIndex()
        if idx >= 0 and idx < len(SPECIAL_QUERIES):
            self.query_editor.setPlainText(SPECIAL_QUERIES[idx]['sql'])
            self.status_label.setText(f"Загружен запрос: {SPECIAL_QUERIES[idx]['name']}")
        else:
            self.query_editor.clear()
            self.status_label.setText('')

    def clear_query(self):
        self.query_editor.clear()
        self.result_table.clear()
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self.status_label.setText('Поле запроса очищено.')

    def execute_current_query(self):
        query = self.query_editor.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "Ошибка", "Введите SQL-запрос перед выполнением.")
            return

        command = query.lstrip().split()[0].upper()
        fetch = command in ('SELECT', 'WITH', 'SHOW', 'EXPLAIN', 'VALUES') or 'RETURNING' in query.upper()

        try:
            logger.info('Executing custom SQL query from query page')
            result = self.db.execute_query(query, fetch=fetch)
            if fetch:
                self.display_query_results(result)
                self.status_label.setText(f"Запрос выполнен. Найдено строк: {len(result)}")
            else:
                self.result_table.clear()
                self.result_table.setRowCount(0)
                self.result_table.setColumnCount(0)
                self.status_label.setText("Запрос выполнен успешно.")
                QMessageBox.information(self, "Успех", "Запрос успешно выполнен.")
        except Exception as e:
            logger.exception('Failed to execute SQL query')
            self.status_label.setText(f"Ошибка выполнения запроса: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось выполнить запрос:\n{str(e)}")

    def display_query_results(self, rows):
        self.result_table.clear()
        if not rows:
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            return

        headers = list(rows[0].keys())
        self.result_table.setColumnCount(len(headers))
        self.result_table.setHorizontalHeaderLabels(headers)
        self.result_table.setRowCount(len(rows))

        for row_idx, row in enumerate(rows):
            for col_idx, header in enumerate(headers):
                value = row.get(header)
                display_value = '' if value is None else str(value)
                item = QTableWidgetItem(display_value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.result_table.setItem(row_idx, col_idx, item)


class BackupWidget(QWidget):
    """Backup management"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.main_window = parent
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("💾 Резервное копирование")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("""
            color: #f1f5f9;
            padding: 8px 0;
        """)
        layout.addWidget(title)

        info = QLabel("Создайте резервную копию базы данных для сохранения текущего состояния.")
        info.setWordWrap(True)
        info.setFont(QFont("Segoe UI", 12))
        info.setStyleSheet("""
            color: #94a3b8;
            padding: 8px;
        """)
        layout.addWidget(info)

        btn_backup = QPushButton("Создать резервную копию")
        btn_backup.setMinimumHeight(50)
        btn_backup.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        btn_backup.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_backup.clicked.connect(self.create_backup)
        layout.addWidget(btn_backup)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setStyleSheet("""
            padding: 16px;
            background: #1e293b;
            border-radius: 8px;
            border: 1px solid #334155;
            color: #f1f5f9;
        """)
        self.status_label.hide()
        layout.addWidget(self.status_label)

        layout.addStretch()
    
    def create_backup(self):
        if not self.main_window.is_superuser:
            QMessageBox.warning(self, "Требуется авторизация", "Для создания бэкапа требуется войти как суперпользователь")
            return
        
        self.status_label.show()
        self.status_label.setText("Создание резервной копии...")
        self.status_label.setStyleSheet("padding: 10px; background: #fef3c7; border-radius: 5px; color: #92400e;")
        
        QApplication.processEvents()
        
        logger.info('Creating backup requested by user')
        result = self.db.create_backup()
        
        if result['status'] == 'success':
            self.status_label.setStyleSheet("""
                padding: 16px;
                background: #052e16;
                border-radius: 8px;
                border: 1px solid #166534;
                color: #4ade80;
            """)
            self.status_label.setText(f"✅ Бэкап успешно создан:\n{result['file']}")
            QMessageBox.information(self, "Успех", "Резервная копия успешно создана")
        else:
            self.status_label.setStyleSheet("""
                padding: 16px;
                background: #2e0505;
                border-radius: 8px;
                border: 1px solid #651616;
                color: #f87171;
            """)
            self.status_label.setText(f"❌ Ошибка: {result.get('message', 'Неизвестная ошибка')}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать бэкап:\n{result.get('message')}")


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.is_superuser = False
        self.current_table_widget = None
        
        self.setup_ui()
        self.show_dashboard()
    
    def setup_ui(self):
        self.setWindowTitle("Автошкола — Система управления")
        self.setGeometry(80, 80, 1400, 900)
        self.setFont(QFont("Segoe UI", 11))
        
        # Central widget with horizontal layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar
        sidebar = self.create_sidebar()
        sidebar.setMaximumWidth(260)
        sidebar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0f172a, stop:1 #1e293b);
        """)
        main_layout.addWidget(sidebar)

        # Content area
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            background: #0f172a;
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        self.page_title = QLabel("Панель управления")
        self.page_title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.page_title.setStyleSheet("""
            color: #f1f5f9;
            padding: 4px 0;
        """)
        header.addWidget(self.page_title)

        header.addStretch()

        self.auth_btn = QPushButton("🔐 Войти как суперпользователь")
        self.auth_btn.setMinimumHeight(36)
        self.auth_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.auth_btn.clicked.connect(self.authenticate)
        header.addWidget(self.auth_btn)

        content_layout.addLayout(header)
        
        # Stacked widget for pages
        self.stacked = QStackedWidget()
        content_layout.addWidget(self.stacked)
        
        main_layout.addWidget(content_frame)
        
        # Status bar
        self.statusBar().showMessage("Готово")
        self.statusBar().setStyleSheet("""
            QStatusBar {
                font-size: 13px;
                padding: 4px;
            }
        """)
    
    def create_sidebar(self):
        sidebar = QWidget()
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Logo
        logo = QLabel("📚 Автошкола")
        logo.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        logo.setStyleSheet("""
            color: #f1f5f9;
            padding: 15px 10px;
            margin-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        """)
        layout.addWidget(logo)

        # Navigation buttons
        self.nav_buttons = {}

        nav_items = [
            ('dashboard', '🏠  Панель управления'),
            ('employees', '👨‍🏫  Сотрудники'),
            ('students', '👨‍🎓  Ученики'),
            ('lessons', '📖  Занятия'),
            ('groups', '👥  Группы'),
            ('positions', '💼  Должности'),
            ('locations', '📍  Места проведения'),
            ('vehicles', '🚗  Автомобили'),
            ('lesson-formats', '📋  Формы обучения'),
            ('queries', '🧪  SQL-запросы'),
        ]

        for key, label in nav_items:
            btn = QPushButton(label)
            btn.setMinimumHeight(42)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("Segoe UI", 13))
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 10px 16px;
                    border: none;
                    border-radius: 8px;
                    color: #cbd5e1;
                    font-size: 13px;
                    margin-bottom: 4px;
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.08);
                    color: #f1f5f9;
                }
                QPushButton:checked {
                    background: #3b82f6;
                    color: white;
                    font-weight: bold;
                }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self.navigate_to(k))
            layout.addWidget(btn)
            self.nav_buttons[key] = btn

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background: rgba(255,255,255,0.08);")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        layout.addSpacing(8)

        # Backup button
        backup_btn = QPushButton("💾  Бэкап")
        backup_btn.setMinimumHeight(42)
        backup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        backup_btn.setFont(QFont("Segoe UI", 13))
        backup_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 16px;
                border: none;
                border-radius: 8px;
                color: #cbd5e1;
                font-size: 13px;
                margin-bottom: 4px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.08);
                color: #f1f5f9;
            }
        """)
        backup_btn.clicked.connect(lambda: self.navigate_to('backup'))
        layout.addWidget(backup_btn)
        
        layout.addStretch()
        
        return sidebar
    
    def navigate_to(self, page):
        # Update nav buttons
        for key, btn in self.nav_buttons.items():
            btn.setChecked(key == page)
        
        # Show appropriate widget
        if page == 'dashboard':
            self.show_dashboard()
        elif page == 'backup':
            self.show_backup()
        elif page == 'queries':
            self.show_queries()
        else:
            self.show_table(page)
    
    def show_dashboard(self):
        self.page_title.setText("Панель управления")
        dashboard = DashboardWidget(self)
        self.set_page_widget(dashboard)
    
    def show_table(self, table_name):
        config = TABLES[table_name]
        self.page_title.setText(config['title'])
        table_widget = DataTableWidget(table_name, self)
        self.set_page_widget(table_widget)
    
    def show_queries(self):
        self.page_title.setText("SQL-запросы")
        queries_widget = SqlQueryWidget(self)
        self.set_page_widget(queries_widget)

    def show_backup(self):
        self.page_title.setText("Резервное копирование")
        backup = BackupWidget(self)
        self.set_page_widget(backup)
    
    def set_page_widget(self, widget):
        # Remove current widget
        if self.stacked.count() > 0:
            old_widget = self.stacked.widget(0)
            self.stacked.removeWidget(old_widget)
            old_widget.deleteLater()
        
        self.stacked.addWidget(widget)
        self.current_table_widget = widget
    
    def authenticate(self):
        password, ok = QInputDialog.getText(
            self, "Авторизация",
            "Введите пароль суперпользователя:",
            QLineEdit.EchoMode.Password
        )
        
        if ok and password:
            if password == CONFIG.get('admin_password', '1234567890'):
                self.is_superuser = True
                self.auth_btn.setText("✅ Суперпользователь")
                self.auth_btn.setStyleSheet("""
                    QPushButton {
                        background: #166534;
                        color: #4ade80;
                        border: 1px solid #22c55e;
                        border-radius: 8px;
                        padding: 8px 15px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #15803d;
                    }
                """)
                self.statusBar().showMessage("Авторизация успешна — суперпользователь")
                logger.info('Superuser successfully authenticated')
                QMessageBox.information(self, "Успех", "Вы вошли как суперпользователь")
            else:
                logger.warning('Superuser authentication failed')
                QMessageBox.critical(self, "Ошибка", "Неверный пароль")
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Выход",
            "Вы уверены, что хотите выйти?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    logger.info('Application starting')
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Set application-wide stylesheet (Dark theme)
    app.setStyleSheet("""
        QMainWindow {
            background: #0f172a;
        }

        QTableWidget {
            background: #1e293b;
            alternate-background-color: #1a2332;
            gridline-color: #334155;
            border: 1px solid #334155;
            border-radius: 10px;
            color: #f1f5f9;
            selection-background-color: #3b82f6;
            selection-color: white;
        }
        QTableWidget::item {
            padding: 10px 8px;
            border-bottom: 1px solid #1e293b;
        }
        QTableWidget::item:hover {
            background: #263545;
        }
        QTableWidget::item:selected {
            background: #3b82f6;
            color: white;
        }
        QHeaderView::section {
            background: #1e293b;
            color: #94a3b8;
            padding: 12px 8px;
            border: none;
            border-bottom: 2px solid #334155;
            font-weight: bold;
            font-size: 12px;
            text-transform: uppercase;
        }
        QTableWidget QTableCornerButton::section {
            background: #1e293b;
            border: 1px solid #334155;
        }
        QScrollBar:vertical {
            background: #1e293b;
            width: 10px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical {
            background: #475569;
            border-radius: 5px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: #64748b;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        QScrollBar:horizontal {
            background: #1e293b;
            height: 10px;
            border-radius: 5px;
        }
        QScrollBar::handle:horizontal {
            background: #475569;
            border-radius: 5px;
            min-width: 20px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #64748b;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0;
        }

        QPushButton {
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 18px;
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton:hover {
            background: #2563eb;
        }
        QPushButton:pressed {
            background: #1d4ed8;
        }
        QPushButton:disabled {
            background: #475569;
            color: #94a3b8;
        }

        QLineEdit {
            padding: 10px 14px;
            background: #1e293b;
            color: #f1f5f9;
            border: 1px solid #334155;
            border-radius: 8px;
            font-size: 13px;
        }
        QLineEdit:focus {
            border-color: #3b82f6;
        }
        QLineEdit::placeholder {
            color: #64748b;
        }

        QComboBox {
            padding: 10px 14px;
            background: #1e293b;
            color: #f1f5f9;
            border: 1px solid #334155;
            border-radius: 8px;
            font-size: 13px;
        }
        QComboBox:hover {
            border-color: #3b82f6;
        }
        QComboBox:focus {
            border-color: #3b82f6;
        }
        QComboBox::drop-down {
            border: none;
            padding-right: 8px;
        }
        QComboBox QAbstractItemView {
            background: #1e293b;
            color: #f1f5f9;
            selection-background-color: #3b82f6;
            border: 1px solid #334155;
        }

        QSpinBox, QDateEdit, QDateTimeEdit {
            padding: 10px 14px;
            background: #1e293b;
            color: #f1f5f9;
            border: 1px solid #334155;
            border-radius: 8px;
            font-size: 13px;
        }
        QSpinBox:hover, QDateEdit:hover, QDateTimeEdit:hover {
            border-color: #3b82f6;
        }
        QSpinBox:focus, QDateEdit:focus, QDateTimeEdit:focus {
            border-color: #3b82f6;
        }
        QSpinBox::up-button, QDateEdit::up-button, QDateTimeEdit::up-button {
            background: #334155;
            border-radius: 6px;
        }
        QSpinBox::down-button, QDateEdit::down-button, QDateTimeEdit::down-button {
            background: #334155;
            border-radius: 6px;
        }

        QTextEdit {
            padding: 10px 14px;
            background: #1e293b;
            color: #f1f5f9;
            border: 1px solid #334155;
            border-radius: 8px;
            font-size: 13px;
        }
        QTextEdit:focus {
            border-color: #3b82f6;
        }

        QLabel {
            color: #f1f5f9;
        }

        QGroupBox {
            font-weight: bold;
            color: #f1f5f9;
            border: 1px solid #334155;
            border-radius: 10px;
            margin-top: 12px;
            padding-top: 16px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: #94a3b8;
        }

        QStackedWidget {
            background: #0f172a;
        }

        QDialog {
            background: #1e293b;
        }
        QDialog QLabel {
            color: #f1f5f9;
        }

        QMessageBox QLabel {
            color: #f1f5f9;
        }
        QMessageBox {
            background: #1e293b;
        }

        QInputDialog {
            background: #1e293b;
        }

        QStatusBar {
            background: #1e293b;
            color: #94a3b8;
            border-top: 1px solid #334155;
        }

        QToolTip {
            background: #1e293b;
            color: #f1f5f9;
            border: 1px solid #334155;
            border-radius: 4px;
            padding: 6px;
        }

        QMenu {
            background: #1e293b;
            color: #f1f5f9;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 4px;
        }
        QMenu::item {
            padding: 8px 24px 8px 12px;
            border-radius: 4px;
        }
        QMenu::item:selected {
            background: #334155;
        }
        QMenuBar {
            background: #1e293b;
            border-bottom: 1px solid #334155;
        }
        QMenuBar::item {
            padding: 8px 12px;
            border-radius: 4px;
        }
        QMenuBar::item:selected {
            background: #334155;
        }
    """)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
