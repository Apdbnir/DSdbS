# Система управления учебным процессом (Educational Process Management System)

Лабораторный практикум по дисциплине «Базы данных» — 2 часть

## Описание

Система для управления учебным процессом (курсанты, преподаватели, группы, занятия, автомобили, места проведения и т.д.)

### Технологии

- **Backend:** Python 3 (HTTP Server, REST API)
- **Database:** PostgreSQL
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **OS:** Windows

## Структура проекта

```
DSdbS/
├── database/                      # SQL скрипты и утилиты БД
│   ├── create_schema.sql         # Создание схемы БД
│   ├── seed_lookup_tables.sql    # Заполнение справочников
│   ├── data_generator.py         # Генератор данных
│   ├── populate_main_tables.sql  # Данные основных таблиц
│   ├── create_functions_triggers.sql  # Функции и триггеры
│   ├── setup_database.bat        # Скрипт установки БД
│   ├── backup_database.bat       # Скрипт бэкапа
│   └── restore_database.bat      # Скрипт восстановления
├── backend/                       # Серверная часть
│   ├── server.py                 # HTTP сервер (REST API)
│   ├── __main__.py               # Точка входа
│   ├── config.json               # Конфигурация
│   └── requirements.txt          # Python зависимости
├── web/                           # Веб-интерфейс
│   ├── index.html                # Главная страница
│   ├── style.css                 # Стили
│   └── app.js                    # JavaScript логика
├── backups/                       # Резервные копии БД
├── logs/                          # Логи сервера
├── start_server.bat              # Запуск сервера
├── README.md                     # Документация
└── .gitignore                    # Игнорируемые файлы
```

## Быстрый старт

### 1. Требования

- Python 3.8+
- PostgreSQL 14+
- Windows OS

### 2. Установка базы данных

1. Убедитесь, что PostgreSQL установлен и запущен
2. Запустите скрипт установки:

```bash
cd database
setup_database.bat
```

Скрипт автоматически:
- Создаст базу данных `educational_process`
- Создаст все таблицы, ограничения, индексы и представления
- Заполнит справочники начальными данными
- Сгенерирует и заполнит основные таблицы (50 сотрудников, 200 курсантов, 300 занятий)
- Создаст функции и триггеры

### 3. Установка зависимостей сервера

```bash
cd backend
pip install -r requirements.txt
```

### 4. Запуск сервера

```bash
start_server.bat
```

Или вручную:

```bash
cd backend
python server.py
```

Сервер запустится на `http://localhost:8080`

### 5. Открытие веб-интерфейса

Откройте `web/index.html` в браузере или перейдите на `http://localhost:8080`

## Конфигурация

### База данных

- **Host:** localhost
- **Port:** 5432
- **Database:** educational_process
- **User:** postgres
- **Password:** postgres

### Сервер

- **Host:** localhost
- **Port:** 8080
- **Superuser Password:** 1234567890

Изменить настройки можно в `backend/config.json`

## API Endpoints

### Основные ресурсы

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/employees` | Список сотрудников |
| GET | `/api/cadets` | Список курсантов |
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

### Пользователь (app_user)

- Просмотр всех таблиц
- Добавление/редактирование/удаление основных таблиц
- Выполнение запросов
- **Не может** редактировать справочники

### Суперпользователь (app_superuser)

- Все права пользователя
- Редактирование справочных таблиц
- Создание бэкапов базы данных

## Бэкап и восстановление

### Создание бэкапа

```bash
cd database
backup_database.bat
```

Или через API (требуется суперпользователь):

```bash
curl -X POST http://localhost:8080/api/backup -H "Authorization: Bearer 1234567890"
```

### Восстановление из бэкапа

```bash
cd database
restore_database.bat backups\educational_process_20260414_120000.sql
```

## Таблицы базы данных

### Справочники (только для суперпользователя)

- `positions` — Должности (10 записей)
- `lesson_formats` — Формы обучения (4 записи)
- `locations` — Места проведения (10 записей)
- `vehicles` — Автомобили (10 записей)
- `groups` — Группы (10 записей)

### Основные таблицы

- `employees` — Сотрудники (50 записей)
- `cadets` — Курсанты (200 записей)
- `lessons` — Занятия (300 записей)
- `cadet_lessons` — Связь курсант-занятие (900+ записей)
- `group_lessons` — Связь группа-занятие (170+ записей)

## Функции и триггеры

### Функции

- `validate_cadet_age()` — Проверка возраста курсанта (>= 16)
- `validate_lesson_format_location()` — Проверка совместимости формата и места
- `count_cadets_in_lesson(lesson_id)` — Количество курсантов на занятии
- `get_lessons_by_date_range(start, end)` — Занятия в диапазоне дат
- `get_cadets_by_group(group_id)` — Курсанты группы
- `get_employee_workload()` — Загрузка преподавателей
- `search_cadets(search_term)` — Поиск курсантов
- `search_employees(search_term)` — Поиск сотрудников

### Представления

- `v_lessons_full` — Полная информация о занятиях
- `v_cadets_full` — Курсанты с группами
- `v_employees_full` — Сотрудники с должностями

## Тестирование с psql

```bash
psql -U postgres -d educational_process

# Проверить таблицы
\dt

# Проверить данные
SELECT COUNT(*) FROM employees;
SELECT COUNT(*) FROM cadets;
SELECT COUNT(*) FROM lessons;

# Проверить представления
SELECT * FROM v_lessons_full LIMIT 5;

# Проверить функции
SELECT * FROM get_employee_workload() LIMIT 10;
```

## Авторы

Разработано в рамках лабораторного практикума по дисциплине «Базы данных»

## Лицензия

MIT
