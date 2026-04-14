/**
 * Educational Process Management System - Web Interface
 */

const API_BASE = 'http://localhost:8080/api';
let authToken = null;
let currentPage = null;
let currentData = [];

// Table configurations
const TABLE_CONFIG = {
    employees: {
        title: 'Сотрудники',
        columns: [
            { key: 'id', label: 'ID', type: 'number', readonly: true },
            { key: 'name', label: 'ФИО', type: 'text' },
            { key: 'experience', label: 'Стаж (лет)', type: 'number' },
            { key: 'email', label: 'Эл.почта', type: 'email' },
            { key: 'phone', label: '№ телефона', type: 'text' },
            { key: 'position_id', label: 'Должность', type: 'select', refTable: 'positions', refLabel: 'name' }
        ]
    },
    cadets: {
        title: 'Курсанты',
        columns: [
            { key: 'id', label: 'ID', type: 'number', readonly: true },
            { key: 'passport_number', label: '№ паспорта', type: 'text' },
            { key: 'full_name', label: 'ФИО', type: 'text' },
            { key: 'medical_certificate', label: 'Мед.справка', type: 'text' },
            { key: 'age', label: 'Возраст', type: 'number' },
            { key: 'group_id', label: 'Группа', type: 'select', refTable: 'groups', refLabel: 'group_number' }
        ]
    },
    lessons: {
        title: 'Занятия',
        columns: [
            { key: 'id', label: 'ID', type: 'number', readonly: true },
            { key: 'name', label: 'Название', type: 'text' },
            { key: 'topic', label: 'Тема', type: 'text' },
            { key: 'lesson_date', label: 'Дата', type: 'date' },
            { key: 'lesson_time', label: 'Время', type: 'time' },
            { key: 'result', label: 'Результат', type: 'text' },
            { key: 'contact_email', label: 'Эл.почта', type: 'email' },
            { key: 'location_id', label: 'Место', type: 'select', refTable: 'locations', refLabel: 'address' },
            { key: 'vehicle_id', label: 'Автомобиль', type: 'select', refTable: 'vehicles', refLabel: 'vehicle_number' },
            { key: 'format_id', label: 'Формат', type: 'select', refTable: 'lesson-formats', refLabel: 'name' },
            { key: 'employee_id', label: 'Сотрудник', type: 'select', refTable: 'employees', refLabel: 'name' }
        ]
    },
    groups: {
        title: 'Группы',
        columns: [
            { key: 'id', label: 'ID', type: 'number', readonly: true },
            { key: 'group_number', label: '№ группы', type: 'text' },
            { key: 'room_number', label: 'Аудитория', type: 'text' },
            { key: 'format_type', label: 'Формат обучения', type: 'text' }
        ]
    },
    positions: {
        title: 'Должности',
        columns: [
            { key: 'id', label: 'ID', type: 'number', readonly: true },
            { key: 'name', label: 'Название', type: 'text' },
            { key: 'phone', label: '№ телефона', type: 'text' },
            { key: 'employment_type', label: 'Тип занятости', type: 'text' },
            { key: 'notes', label: 'Замечания', type: 'textarea' }
        ]
    },
    locations: {
        title: 'Места проведения',
        columns: [
            { key: 'id', label: 'ID', type: 'number', readonly: true },
            { key: 'geolocation', label: 'Геолокация', type: 'text' },
            { key: 'location_type', label: 'Тип помещения', type: 'text' },
            { key: 'address', label: 'Адрес', type: 'text' },
            { key: 'responsible_employee_id', label: 'Ответственный', type: 'select', refTable: 'employees', refLabel: 'name' }
        ]
    },
    vehicles: {
        title: 'Автомобили',
        columns: [
            { key: 'id', label: 'ID', type: 'number', readonly: true },
            { key: 'vehicle_number', label: '№ автомобиля', type: 'text' },
            { key: 'route', label: 'Маршрут', type: 'text' },
            { key: 'notes', label: 'Замечания', type: 'textarea' },
            { key: 'category', label: 'Категория', type: 'text' }
        ]
    },
    'lesson-formats': {
        title: 'Формы обучения',
        columns: [
            { key: 'id', label: 'ID', type: 'number', readonly: true },
            { key: 'name', label: 'Название', type: 'text' }
        ]
    }
};

// ==========================================================================
// Initialization
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    initializeAuth();
    initializeSearch();
    initializeRefresh();
    loadDashboard();
});

function initializeNavigation() {
    const navBtns = document.querySelectorAll('.nav-btn');
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const page = btn.dataset.page;
            navigateToPage(page);
        });
    });
}

function initializeAuth() {
    document.getElementById('authBtn').addEventListener('click', authenticate);
    document.getElementById('logoutBtn').addEventListener('click', logout);
}

function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            if (currentPage && currentPage !== 'dashboard' && currentPage !== 'queries' && currentPage !== 'backup') {
                filterData(e.target.value);
            }
        }, 300);
    });
}

function initializeRefresh() {
    document.getElementById('refreshBtn').addEventListener('click', () => {
        if (currentPage && currentPage !== 'dashboard') {
            loadTableData(currentPage);
        } else if (currentPage === 'dashboard') {
            loadDashboard();
        }
    });
}

// ==========================================================================
// Navigation
// ==========================================================================

function navigateToPage(page) {
    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-page="${page}"]`)?.classList.add('active');
    
    // Update pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    
    currentPage = page;
    
    if (page === 'dashboard') {
        document.getElementById('dashboard-page').classList.add('active');
        document.getElementById('pageTitle').textContent = 'Панель управления';
        document.getElementById('searchInput').style.display = 'none';
        loadDashboard();
    } else if (page === 'queries') {
        document.getElementById('queries-page').classList.add('active');
        document.getElementById('pageTitle').textContent = 'Специальные запросы';
        document.getElementById('searchInput').style.display = 'none';
        initializeQueries();
    } else if (page === 'backup') {
        document.getElementById('backup-page').classList.add('active');
        document.getElementById('pageTitle').textContent = 'Бэкап базы данных';
        document.getElementById('searchInput').style.display = 'none';
        initializeBackup();
    } else if (TABLE_CONFIG[page]) {
        document.getElementById('table-page').classList.add('active');
        document.getElementById('pageTitle').textContent = TABLE_CONFIG[page].title;
        document.getElementById('searchInput').style.display = 'block';
        loadTableData(page);
    }
}

// ==========================================================================
// Dashboard
// ==========================================================================

async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE}/statistics`);
        const stats = await response.json();
        
        document.getElementById('stat-employees').textContent = stats.employees || 0;
        document.getElementById('stat-cadets').textContent = stats.cadets || 0;
        document.getElementById('stat-lessons').textContent = stats.lessons || 0;
        document.getElementById('stat-groups').textContent = stats.groups || 0;
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

// ==========================================================================
// Table Data Loading
// ==========================================================================

async function loadTableData(tableName) {
    try {
        const response = await fetch(`${API_BASE}/${tableName}?limit=1000`);
        const data = await response.json();
        currentData = data;
        renderTable(tableName, data);
    } catch (error) {
        showNotification('Ошибка загрузки данных', 'error');
        console.error(error);
    }
}

function renderTable(tableName, data) {
    const config = TABLE_CONFIG[tableName];
    const thead = document.getElementById('tableHead');
    const tbody = document.getElementById('tableBody');
    
    // Clear table
    thead.innerHTML = '';
    tbody.innerHTML = '';
    
    // Create header
    const headerRow = document.createElement('tr');
    config.columns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col.label;
        headerRow.appendChild(th);
    });
    
    // Actions column
    const actionTh = document.createElement('th');
    actionTh.textContent = 'Действия';
    headerRow.appendChild(actionTh);
    
    thead.appendChild(headerRow);
    
    // Create rows
    data.forEach(row => {
        const tr = document.createElement('tr');
        
        config.columns.forEach(col => {
            const td = document.createElement('td');
            let value = row[col.key];
            
            // Format value based on type
            if (value === null || value === undefined) {
                value = '-';
            } else if (col.type === 'date' && value) {
                value = new Date(value).toLocaleDateString('ru-RU');
            }
            
            td.textContent = value;
            tr.appendChild(td);
        });
        
        // Actions
        const actionTd = document.createElement('td');
        const editBtn = document.createElement('button');
        editBtn.className = 'action-btn edit-btn';
        editBtn.textContent = '✏️';
        editBtn.onclick = () => openEditModal(tableName, row);
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'action-btn delete-btn';
        deleteBtn.textContent = '🗑️';
        deleteBtn.onclick = () => deleteRecord(tableName, row);
        
        actionTd.appendChild(editBtn);
        actionTd.appendChild(deleteBtn);
        tr.appendChild(actionTd);
        
        tbody.appendChild(tr);
    });
    
    // Setup add button
    document.getElementById('addBtn').onclick = () => openAddModal(tableName);
}

function filterData(searchTerm) {
    if (!searchTerm) {
        renderTable(currentPage, currentData);
        return;
    }
    
    const filtered = currentData.filter(row => {
        return Object.values(row).some(val => 
            val && val.toString().toLowerCase().includes(searchTerm.toLowerCase())
        );
    });
    
    renderTable(currentPage, filtered);
}

// ==========================================================================
// Modal Dialogs
// ==========================================================================

function openAddModal(tableName) {
    const config = TABLE_CONFIG[tableName];
    const modal = document.getElementById('modal');
    const form = document.getElementById('modalForm');
    const title = document.getElementById('modalTitle');
    
    title.textContent = `Добавить запись - ${config.title}`;
    form.innerHTML = '';
    
    config.columns.forEach(col => {
        if (col.readonly) return;
        
        const formGroup = document.createElement('div');
        formGroup.className = 'form-group';
        
        const label = document.createElement('label');
        label.textContent = col.label;
        label.htmlFor = `field-${col.key}`;
        
        let input;
        if (col.type === 'select' && col.refTable) {
            input = document.createElement('select');
            loadSelectOptions(input, col.refTable, col.key);
        } else if (col.type === 'textarea') {
            input = document.createElement('textarea');
            input.rows = 3;
        } else {
            input = document.createElement('input');
            input.type = col.type || 'text';
        }
        
        input.id = `field-${col.key}`;
        input.name = col.key;
        input.required = !col.readonly;
        
        formGroup.appendChild(label);
        formGroup.appendChild(input);
        form.appendChild(formGroup);
    });
    
    modal.classList.add('active');
    
    // Setup form submission
    form.onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const data = {};
        
        config.columns.forEach(col => {
            if (!col.readonly) {
                const value = formData.get(col.key);
                if (value) {
                    data[col.key] = value === '' ? null : value;
                }
            }
        });
        
        await createRecord(tableName, data);
    };
}

async function loadSelectOptions(selectElement, refTable, fieldName) {
    try {
        const response = await fetch(`${API_BASE}/${refTable}?limit=1000`);
        const data = await response.json();
        
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = '-- Выберите --';
        selectElement.appendChild(defaultOption);
        
        data.forEach(item => {
            const option = document.createElement('option');
            option.value = item.id;
            option.textContent = item.name || item[Object.keys(item)[1]] || item.id;
            selectElement.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load options:', error);
    }
}

function openEditModal(tableName, row) {
    const config = TABLE_CONFIG[tableName];
    const modal = document.getElementById('modal');
    const form = document.getElementById('modalForm');
    const title = document.getElementById('modalTitle');
    
    title.textContent = `Редактировать запись - ${config.title}`;
    form.innerHTML = '';
    
    config.columns.forEach(col => {
        const formGroup = document.createElement('div');
        formGroup.className = 'form-group';
        
        const label = document.createElement('label');
        label.textContent = col.label;
        label.htmlFor = `field-${col.key}`;
        
        let input;
        if (col.type === 'select' && col.refTable) {
            input = document.createElement('select');
            loadSelectOptions(input, col.refTable, col.key).then(() => {
                input.value = row[col.key] || '';
            });
        } else if (col.type === 'textarea') {
            input = document.createElement('textarea');
            input.rows = 3;
            input.value = row[col.key] || '';
        } else {
            input = document.createElement('input');
            input.type = col.type || 'text';
            input.value = row[col.key] !== null && row[col.key] !== undefined ? row[col.key] : '';
            if (col.type === 'date' && input.value) {
                input.value = input.value.split('T')[0];
            }
        }
        
        input.id = `field-${col.key}`;
        input.name = col.key;
        input.readOnly = col.readonly || false;
        
        formGroup.appendChild(label);
        formGroup.appendChild(input);
        form.appendChild(formGroup);
    });
    
    modal.classList.add('active');
    
    // Setup form submission
    form.onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const data = {};
        
        config.columns.forEach(col => {
            if (!col.readonly) {
                const value = formData.get(col.key);
                if (value) {
                    data[col.key] = value === '' ? null : value;
                }
            }
        });
        
        await updateRecord(tableName, row.id, data);
    };
}

document.getElementById('closeModal').addEventListener('click', () => {
    document.getElementById('modal').classList.remove('active');
});

document.getElementById('cancelBtn').addEventListener('click', () => {
    document.getElementById('modal').classList.remove('active');
});

// ==========================================================================
// CRUD Operations
// ==========================================================================

async function createRecord(tableName, data) {
    try {
        const headers = { 'Content-Type': 'application/json' };
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        const response = await fetch(`${API_BASE}/${tableName}`, {
            method: 'POST',
            headers,
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showNotification('Запись успешно добавлена');
            document.getElementById('modal').classList.remove('active');
            loadTableData(tableName);
        } else {
            const error = await response.json();
            showNotification(error.error || 'Ошибка добавления', 'error');
        }
    } catch (error) {
        showNotification('Ошибка соединения', 'error');
    }
}

async function updateRecord(tableName, id, data) {
    try {
        const headers = { 'Content-Type': 'application/json' };
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        const response = await fetch(`${API_BASE}/${tableName}/${id}`, {
            method: 'PUT',
            headers,
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showNotification('Запись успешно обновлена');
            document.getElementById('modal').classList.remove('active');
            loadTableData(tableName);
        } else {
            const error = await response.json();
            showNotification(error.error || 'Ошибка обновления', 'error');
        }
    } catch (error) {
        showNotification('Ошибка соединения', 'error');
    }
}

async function deleteRecord(tableName, row) {
    if (!confirm('Вы уверены, что хотите удалить эту запись?')) {
        return;
    }
    
    try {
        const headers = {};
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        const response = await fetch(`${API_BASE}/${tableName}/${row.id}`, {
            method: 'DELETE',
            headers
        });
        
        if (response.ok) {
            showNotification('Запись успешно удалена');
            loadTableData(tableName);
        } else {
            const error = await response.json();
            showNotification(error.error || 'Ошибка удаления', 'error');
        }
    } catch (error) {
        showNotification('Ошибка соединения', 'error');
    }
}

// ==========================================================================
// Authentication
// ==========================================================================

async function authenticate() {
    const password = prompt('Введите пароль суперпользователя:');
    if (!password) return;
    
    try {
        // Test authentication by trying to access a lookup table operation
        const response = await fetch(`${API_BASE}/positions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${password}`
            },
            body: JSON.stringify({})
        });
        
        if (response.status === 403) {
            showNotification('Неверный пароль', 'error');
            return;
        }
        
        // Authentication successful
        authToken = password;
        document.getElementById('authBtn').style.display = 'none';
        document.getElementById('authStatus').style.display = 'flex';
        showNotification('Авторизация успешна');
    } catch (error) {
        showNotification('Ошибка соединения', 'error');
    }
}

function logout() {
    authToken = null;
    document.getElementById('authBtn').style.display = 'block';
    document.getElementById('authStatus').style.display = 'none';
    showNotification('Вы вышли из системы');
}

// ==========================================================================
// Special Queries
// ==========================================================================

function initializeQueries() {
    const queryBtns = document.querySelectorAll('.query-btn');
    queryBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const query = btn.dataset.query;
            executeQuery(query);
        });
    });
}

async function executeQuery(queryName) {
    const resultDiv = document.getElementById('queryResult');
    resultDiv.innerHTML = '<p>Выполняется запрос...</p>';
    
    try {
        let sql;
        switch (queryName) {
            case 'lessons-full':
                sql = 'SELECT * FROM public.v_lessons_full LIMIT 50';
                break;
            case 'cadets-full':
                sql = 'SELECT * FROM public.v_cadets_full LIMIT 50';
                break;
            case 'employees-full':
                sql = 'SELECT * FROM public.v_employees_full LIMIT 50';
                break;
            case 'employee-workload':
                sql = 'SELECT * FROM public.get_employee_workload()';
                break;
            default:
                resultDiv.innerHTML = '<p>Неизвестный запрос</p>';
                return;
        }
        
        // Use custom query endpoint (would need to be implemented on server)
        resultDiv.innerHTML = '<p>Для выполнения специальных запросов используйте psql или добавьте endpoint на сервере</p>';
        
    } catch (error) {
        resultDiv.innerHTML = `<p>Ошибка: ${error.message}</p>`;
    }
}

// ==========================================================================
// Backup
// ==========================================================================

function initializeBackup() {
    const backupBtn = document.getElementById('createBackupBtn');
    backupBtn.addEventListener('click', createBackup);
}

async function createBackup() {
    const statusDiv = document.getElementById('backupStatus');
    statusDiv.innerHTML = '<p>Создание резервной копии...</p>';
    
    if (!authToken) {
        statusDiv.innerHTML = '<p style="color: var(--danger);">Требуется авторизация суперпользователя</p>';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/backup`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            statusDiv.innerHTML = `<p style="color: var(--success);">✓ Бэкап успешно создан: ${result.file}</p>`;
            showNotification('Бэкап успешно создан');
        } else {
            statusDiv.innerHTML = `<p style="color: var(--danger);">✗ Ошибка: ${result.message}</p>`;
            showNotification('Ошибка создания бэкапа', 'error');
        }
    } catch (error) {
        statusDiv.innerHTML = `<p style="color: var(--danger);">✗ Ошибка: ${error.message}</p>`;
        showNotification('Ошибка соединения', 'error');
    }
}

// ==========================================================================
// Notifications
// ==========================================================================

function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('active');
    
    setTimeout(() => {
        notification.classList.remove('active');
    }, 3000);
}
