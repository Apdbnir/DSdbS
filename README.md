# Система управления автошколой (Driving School Database System)

Лабораторный практикум по дисциплине «Базы данных» — 2 часть

## Описание

Система для управления учебным процессом автошколы — ученики, инструкторы, группы, занятия, учебные автомобили, места проведения и расписание.

### Технологии

- **Backend:** Python 3 (HTTP Server, REST API, psycopg2)
- **Desktop-приложение:** Python 3 (PyQt6)
- **Database:** PostgreSQL
- **OS:** Windows

## Структура проекта

```
DSdbS/
├── database/                      # SQL скрипты и утилиты БД
│   ├── create_schema.sql          # Создание схемы БД
│   ├── seed_lookup_tables.sql     # Заполнение справочников
│   ├── data_generator.py          # Генератор данных
│   ├── populate_main_tables.sql   # Данные основных таблиц
│   ├── create_functions_triggers.sql  # Функции и триггеры
│   ├── setup_database.bat         # Скрипт установки БД
│   ├── backup_database.bat        # Скрипт бэкапа
│   ├── restore_database.bat       # Скрипт восстановления
│   └── verify_database.bat        # Проверка БД
├── backend/                       # Серверная часть и приложение
│   ├── server.py                  # HTTP сервер (REST API)
│   ├── app.py                     # Desktop-приложение (PyQt6)
│   ├── __main__.py                # Точка входа сервера
│   ├── config.json                # Конфигурация
│   └── requirements.txt           # Python зависимости
├── backups/                       # Резервные копии БД
├── logs/                          # Логи сервера
├── start_server.bat               # Запуск сервера
├── start_app.bat                  # Запуск desktop-приложения
├── README.md                      # Документация
└── .gitignore                     # Игнорируемые файлы
```

## Быстрый старт

### 1. Требования

- Python 3.8+
- PostgreSQL 14+
- Windows OS

### 2. Установка базы данных

1. Убедитесь, что PostgreSQL установлен и запущен
2. Запустите скрипт установки:

```
cd database
setup_database.bat
```

Скрипт автоматически:
- Создаст базу данных `driving_school`
- Создаст все таблицы, ограничения, индексы и представления
- Заполнит справочники начальными данными
- Сгенерирует и заполнит основные таблицы (50 сотрудников, 200 учеников, 300 занятий)
- Создаст функции и триггеры

### 3. Установка зависимостей

```
cd backend
pip install -r requirements.txt
```

### 4. Запуск desktop-приложения

```
start_app.bat
```

Или вручную:

```
cd backend
python app.py
```

### 5. Запуск HTTP-сервера (опционально)

```
start_server.bat
```

Сервер запустится на `http://localhost:8080`

## Конфигурация

### База данных

- **Host:** localhost
- **Port:** 5432
- **Database:** driving_school
- **User:** postgres
- **Password:** postgres

### Приложение

- **Superuser пароль:** 1234567890

Изменить настройки можно в `backend/config.json`

## API Endpoints (HTTP-сервер)

### Основные ресурсы

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/employees` | Список сотрудников |
| GET | `/api/students` | Список учеников |
| GET | `/api/lessons` | Список занятий |
| GET | `/api/groups` | Список групп |
| GET | `/api/positions` | Список должностей |
| GET | `/api/locations` | Список мест проведения |
| GET | `/api/vehicles` | Список автомобилей |
| GET | `/api/lesson-formats` | Список форм обучения |

### CRUD операции

- `GET /api/{resource}` — Получить все записи
- `GET /api/{resource}/{id}` — Получить одну запись
- `POST /api/{resource}` — Создать запись
- `PUT /api/{resource}/{id}` — Обновить запись
- `DELETE /api/{resource}/{id}` — Удалить запись

### Специальные endpoints

- `GET /api/statistics` — Статистика БД
- `POST /api/backup` — Создать бэкап (только суперпользователь)

### Параметры запросов

- `?limit=100` — Лимит записей
- `?offset=0` — Смещение
- `?field=value` — Фильтрация по полю

### Авторизация

Для редактирования справочных таблиц и создания бэкапов требуется авторизация суперпользователя:

```
Authorization: Bearer 1234567890
```

## Роли и права

### Пользователь

- Просмотр всех таблиц
- Добавление/редактирование/удаление основных таблиц
- Выполнение запросов
- **Не может** редактировать справочники

### Суперпользователь

- Все права пользователя
- Редактирование справочных таблиц
- Создание бэкапов базы данных

## Бэкап и восстановление

### Создание бэкапа

```
cd database
backup_database.bat
```

Или через API (требуется суперпользователь):

```
curl -X POST http://localhost:8080/api/backup -H "Authorization: Bearer 1234567890"
```

### Восстановление из бэкапа

```
cd database
restore_database.bat backups\driving_school_20260414_120000.sql
```

## Таблицы базы данных

### Справочники (только для суперпользователя)

- `positions` — Должности (10 записей)
- `lesson_formats` — Формы обучения (4 записи: Очно, Дистанционно, Выездной, Смешанно)
- `locations` — Места проведения (10 записей)
- `vehicles` — Учебные автомобили (10 записей)
- `groups` — Учебные группы (10 записей)

### Основные таблицы

- `employees` — Сотрудники/Инструкторы (50 записей)
- `students` — Ученики/Курсанты (200 записей)
- `lessons` — Занятия по вождению (300 записей)
- `student_lessons` — Посещаемость учеников (900+ записей)
- `group_lessons` — Расписание групп (170+ записей)

## Функции и триггеры

### Функции

- `validate_student_age()` — Проверка возраста ученика (>= 16)
- `validate_lesson_format_location()` — Проверка совместимости формата и места
- `count_students_in_lesson(lesson_id)` — Количество учеников на занятии
- `get_lessons_by_date_range(start, end)` — Занятия в диапазоне дат
- `get_students_by_group(group_id)` — Ученики группы
- `get_instructor_workload()` — Загрузка инструкторов
- `search_students(search_term)` — Поиск учеников
- `search_employees(search_term)` — Поиск сотрудников

### Представления

- `v_lessons_full` — Полная информация о занятиях
- `v_students_full` — Ученики с группами
- `v_employees_full` — Сотрудники с должностями

## Тестирование с psql

```
psql -U postgres -d driving_school

-- Проверить таблицы
\dt

-- Проверить данные
SELECT COUNT(*) FROM employees;
SELECT COUNT(*) FROM students;
SELECT COUNT(*) FROM lessons;

-- Проверить представления
SELECT * FROM v_lessons_full LIMIT 5;

-- Проверить функции
SELECT * FROM get_instructor_workload() LIMIT 10;
```

## Desktop-приложение (PyQt6)

### Возможности

- ✅ Панель управления со статистикой
- ✅ Таблицы с добавлением/редактированием/удалением
- ✅ Поиск и фильтрация данных
- ✅ Выпадающие списки для внешних ключей
- ✅ Создание бэкапов
- ✅ Авторизация суперпользователя
- ✅ Приятный современный интерфейс

### Запуск

```
start_app.bat
```

Или:

```
cd backend
python app.py
```

## Решение проблем

### Ошибка: "psql.exe not found"
- Укажите правильный путь к PostgreSQL в файле `setup_database.bat`
- Измените строку: `set PG_BIN=C:\Program Files\PostgreSQL\16\bin`
- Для PostgreSQL 15: `C:\Program Files\PostgreSQL\15\bin`
- Для PostgreSQL 14: `C:\Program Files\PostgreSQL\14\bin`

### Ошибка: "connection refused"
- Убедитесь, что PostgreSQL запущен
- Проверьте, что база данных `driving_school` существует

### Ошибка: "module psycopg2 not found"
- Установите зависимости: `pip install -r backend/requirements.txt`

### Ошибка: "module PyQt6 not found"
- Установите зависимости: `pip install -r backend/requirements.txt`

### Сервер не запускается
- Проверьте, что порт 8080 свободен
- Измените порт в `backend/config.json`

## Авторы

Разработано в рамках лабораторного практикума по дисциплине «Базы данных»

## Лицензия

MIT
