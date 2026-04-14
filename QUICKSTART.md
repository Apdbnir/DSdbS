# РУКОВОДСТВО ПО УСТАНОВКЕ И ЗАПУСКУ

## Быстрый старт (3 шага)

### Шаг 1: Установка базы данных

1. Убедитесь, что PostgreSQL 14+ установлен и запущен
2. Откройте командную строку (cmd)
3. Перейдите в папку database:
   ```
   cd C:\VS_Code\DSdbS\database
   ```
4. Запустите:
   ```
   setup_database.bat
   ```

Скрипт автоматически создаст и заполнит базу данных.

### Шаг 2: Установка Python зависимостей

1. Откройте командную строку
2. Перейдите в папку backend:
   ```
   cd C:\VS_Code\DSdbS\backend
   ```
3. Создайте виртуальное окружение:
   ```
   python -m venv venv
   ```
4. Активируйте:
   ```
   venv\Scripts\activate
   ```
5. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

### Шаг 3: Запуск сервера

1. Вернитесь в корневую папку:
   ```
   cd C:\VS_Code\DSdbS
   ```
2. Запустите сервер:
   ```
   start_server.bat
   ```
3. Откройте `web\index.html` в браузере

**ГОТОВО!** Система запущена на http://localhost:8080

---

## Проверка установки

### Проверка базы данных

```
cd database
verify_database.bat
```

Покажет все таблицы, количество записей, функции и триггеры.

### Проверка сервера

Откройте браузер и перейдите:
```
http://localhost:8080/api/statistics
```

Должен вернуться JSON с количеством записей в каждой таблице.

---

## Параметры по умолчанию

### PostgreSQL
- Host: localhost
- Port: 5432
- Database: educational_process
- User: postgres
- Password: postgres

### Сервер
- URL: http://localhost:8080
- Superuser пароль: 1234567890

---

## Структура базы данных

### Справочники (только для суперпользователя)
1. **positions** - Должности (10 записей)
2. **lesson_formats** - Формы обучения (4 записи: Очно, Дистанционно, Выездной, Смешанно)
3. **locations** - Места проведения (10 записей)
4. **vehicles** - Автомобили (10 записей)
5. **groups** - Группы (10 записей)

### Основные таблицы
1. **employees** - Сотрудники (50 записей)
2. **cadets** - Курсанты (200 записей)
3. **lessons** - Занятия (300 записей)

### Таблицы связей
1. **cadet_lessons** - Курсант-Занятия (900+ записей)
2. **group_lessons** - Группа-Занятия (170+ записей)

---

## API Endpoints

### CRUD операции
```
GET    /api/{table}              - Получить все записи
GET    /api/{table}/{id}         - Получить одну запись
POST   /api/{table}              - Создать запись
PUT    /api/{table}/{id}         - Обновить запись
DELETE /api/{table}/{id}         - Удалить запись
```

### Доступные таблицы
- `/api/employees` - Сотрудники
- `/api/cadets` - Курсанты
- `/api/lessons` - Занятия
- `/api/groups` - Группы
- `/api/positions` - Должности
- `/api/locations` - Места проведения
- `/api/vehicles` - Автомобили
- `/api/lesson-formats` - Формы обучения
- `/api/cadet-lessons` - Связь курсант-занятие
- `/api/group-lessons` - Связь группа-занятие

### Специальные endpoints
```
GET  /api/statistics    - Статистика БД
POST /api/backup        - Создать бэкап (суперпользователь)
```

### Параметры запросов
```
?limit=100              - Лимит записей (по умолчанию 100)
?offset=0               - Смещение (по умолчанию 0)
?field=value            - Фильтрация по полю
```

### Примеры запросов

Получить всех курсантов:
```
GET http://localhost:8080/api/cadets
```

Получить курсанта с ID=5:
```
GET http://localhost:8080/api/cadets/5
```

Создать нового сотрудника:
```
POST http://localhost:8080/api/employees
Content-Type: application/json

{
  "name": "Тестовый Пользователь",
  "experience": 5,
  "email": "test@example.com",
  "phone": "+7(900)123-45-67",
  "position_id": 1
}
```

Редактировать занятие (требуется суперпользователь):
```
PUT http://localhost:8080/api/lessons/1
Authorization: Bearer 1234567890
Content-Type: application/json

{
  "topic": "Новая тема"
}
```

---

## Роли и права

### Пользователь
✅ Просмотр всех таблиц
✅ Добавление/редактирование/удаление основных таблиц
✅ Выполнение запросов
❌ Редактирование справочников

### Суперпользователь
✅ Все права пользователя
✅ Редактирование справочных таблиц
✅ Создание бэкапов

Для авторизации как суперпользователь в веб-интерфейсе нажмите кнопку "Войти как суперпользователь" и введите пароль: `1234567890`

---

## Бэкап и восстановление

### Создание бэкапа

**Способ 1: Через скрипт**
```
cd database
backup_database.bat
```

**Способ 2: Через API**
```bash
curl -X POST http://localhost:8080/api/backup -H "Authorization: Bearer 1234567890"
```

Бэкапы сохраняются в папку `backups/`

### Восстановление из бэкапа

```
cd database
restore_database.bat backups\educational_process_20260414_120000.sql
```

⚠️ **Внимание:** Это удалит текущую базу данных и создаст новую из бэкапа!

---

## Функции базы данных

### Проверочные триггеры
- `trg_validate_cadet_age` - Проверяет, что возраст курсанта >= 16
- `trg_validate_format_location` - Проверяет совместимость формата и места занятия

### Функции для запросов
- `count_cadets_in_lesson(lesson_id)` - Количество курсантов на занятии
- `get_lessons_by_date_range(start_date, end_date)` - Занятия в диапазоне дат
- `get_cadets_by_group(group_id)` - Все курсанты группы
- `get_employee_workload()` - Загрузка преподавателей
- `search_cadets(search_term)` - Поиск курсантов по имени/паспорту
- `search_employees(search_term)` - Поиск сотрудников

### Представления (Views)
- `v_lessons_full` - Полная информация о занятиях
- `v_cadets_full` - Курсанты с группами
- `v_employees_full` - Сотрудники с должностями

---

## Решение проблем

### Ошибка: "psql.exe not found"
- Укажите правильный путь к PostgreSQL в файле `setup_database.bat`
- Измените строку: `set PG_BIN=C:\Program Files\PostgreSQL\16\bin`
- Для PostgreSQL 15: `C:\Program Files\PostgreSQL\15\bin`
- Для PostgreSQL 14: `C:\Program Files\PostgreSQL\14\bin`

### Ошибка: "connection refused"
- Убедитесь, что PostgreSQL запущен
- Проверьте, что база данных `educational_process` существует

### Ошибка: "module psycopg2 not found"
- Установите зависимости: `pip install -r backend/requirements.txt`

### Сервер не запускается
- Проверьте, что порт 8080 свободен
- Измените порт в `backend/config.json`

---

## Тестирование с psql

```bash
psql -U postgres -d educational_process

# Посмотреть все таблицы
\dt

# Посмотреть структуру таблицы
\d employees

# Проверить количество записей
SELECT COUNT(*) FROM employees;
SELECT COUNT(*) FROM cadets;
SELECT COUNT(*) FROM lessons;

# Проверить представление
SELECT * FROM v_lessons_full LIMIT 5;

# Вызвать функцию
SELECT * FROM get_employee_workload() LIMIT 10;

# Выйти
\q
```

---

## Генерация новых данных

Для перегенерации данных выполните:

```
cd database
python data_generator.py
psql -U postgres -d educational_process -f populate_main_tables.sql
```

Данные генерируются случайным образом, но воспроизводимо (seed=42).

---

## Поддержка

При проблемах обращайтесь к:
1. README.md - основная документация
2. Логам сервера: `logs/server.log`
3. Логам ошибок: `logs/error.log`
