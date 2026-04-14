"""
Educational Process Management System - Desktop Application (PyQt6)
"""

import sys
import json
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QComboBox, QSpinBox, QDateEdit, QTextEdit, QDialog, QFormLayout,
    QDialogButtonBox, QMessageBox, QHeaderView, QSplitter, QTreeWidget,
    QTreeWidgetItem, QStackedWidget, QToolBar, QStatusBar, QInputDialog,
    QFileDialog, QFrame, QGroupBox, QGridLayout, QTabWidget
)
from PyQt6.QtCore import Qt, QDate, QTime, QSize
from PyQt6.QtGui import QAction, QIcon, QFont, QColor, QPixmap
import psycopg2
import psycopg2.extras
from datetime import datetime

# Load configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.db_config = CONFIG['database']
        self.lookup_tables = CONFIG.get('lookup_tables', [])
    
    def get_connection(self):
        return psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            dbname=self.db_config['name'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            client_encoding='utf8'
        )
    
    def execute_query(self, query, params=None, fetch=True):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(query, params)
            
            if fetch:
                result = cursor.fetchall()
                result = [self._serialize_row(row) for row in result]
                cursor.close()
                conn.close()
                return result
            else:
                conn.commit()
                cursor.close()
                conn.close()
                return True
        except Exception as e:
            if conn:
                conn.rollback()
                conn.close()
            raise
    
    def _serialize_row(self, row):
        serialized = {}
        for key, value in row.items():
            if hasattr(value, 'isoformat'):
                serialized[key] = value.isoformat()
            elif isinstance(value, str):
                # Ensure string is valid UTF-8
                try:
                    serialized[key] = value.encode('utf-8').decode('utf-8')
                except (UnicodeEncodeError, UnicodeDecodeError):
                    serialized[key] = value.encode('cp1251', errors='replace').decode('utf-8', errors='replace')
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
            self.current_data = self.db.get_all(self.table_name, filters)
            self.populate_table()
        except Exception as e:
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
                self.db.create(self.table_name, data)
                QMessageBox.information(self, "Успех", "Запись успешно добавлена")
                self.load_data()
            except Exception as e:
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
                
                self.db.update(self.table_name, record_id, data)
                QMessageBox.information(self, "Успех", "Запись успешно обновлена")
                self.load_data()
            except Exception as e:
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
                
                self.db.delete(self.table_name, record_id)
                QMessageBox.information(self, "Успех", "Запись успешно удалена")
                self.load_data()
            except Exception as e:
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
            print(f"Failed to load stats: {e}")
    
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
                QMessageBox.information(self, "Успех", "Вы вошли как суперпользователь")
            else:
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
