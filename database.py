import sqlite3
from datetime import datetime, timedelta
from config import DATABASE_PATH, WORKING_HOURS, SERVICES


def init_database():
    """Инициализация базы данных с новыми таблицами и миграцией"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Создаем таблицу записей (базовая версия для совместимости)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            appointment_date DATE NOT NULL,
            appointment_time TIME NOT NULL,
            service TEXT NOT NULL
        )
    ''')

    # Проверяем и добавляем новые колонки если их нет
    cursor.execute("PRAGMA table_info(appointments)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'telegram_user_id' not in columns:
        cursor.execute('ALTER TABLE appointments ADD COLUMN telegram_user_id INTEGER')
        print("✅ Добавлена колонка telegram_user_id")

    if 'phone' not in columns:
        cursor.execute('ALTER TABLE appointments ADD COLUMN phone TEXT')
        print("✅ Добавлена колонка phone")

    if 'status' not in columns:
        cursor.execute('ALTER TABLE appointments ADD COLUMN status TEXT DEFAULT "active"')
        cursor.execute('UPDATE appointments SET status = "active" WHERE status IS NULL')
        print("✅ Добавлена колонка status")

    if 'created_at' not in columns:
        cursor.execute('ALTER TABLE appointments ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        print("✅ Добавлена колонка created_at")

    if 'updated_at' not in columns:
        cursor.execute('ALTER TABLE appointments ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        print("✅ Добавлена колонка updated_at")

    # Создаем таблицу клиентов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER UNIQUE,
            name TEXT,
            phone TEXT,
            first_visit DATE,
            last_visit DATE,
            total_visits INTEGER DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Создаем индексы для быстрого поиска (только если колонки существуют)
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointment_date ON appointments(appointment_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_telegram_user_id ON appointments(telegram_user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_telegram_id ON clients(telegram_user_id)')
        print("✅ Индексы созданы")
    except sqlite3.OperationalError as e:
        print(f"⚠️ Ошибка создания индексов: {e}")

    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")


# ===== ФУНКЦИИ ДЛЯ АДМИНИСТРАТОРА =====

def get_schedule_by_date(date_offset=0):
    """Получает расписание на определенную дату (для админа)"""
    target_date = datetime.now().date() + timedelta(days=date_offset)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT client_name, appointment_time, service 
        FROM appointments 
        WHERE appointment_date = ? AND status = 'active'
        ORDER BY appointment_time
    ''', (target_date,))
    appointments = cursor.fetchall()
    conn.close()

    return appointments, target_date


def get_schedule_by_specific_date(date_str):
    """Получает расписание на конкретную дату (для админа)"""
    try:
        target_date = datetime.strptime(date_str, '%d.%m.%Y').date()

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, client_name, appointment_time, service 
            FROM appointments 
            WHERE appointment_date = ? AND status = 'active'
            ORDER BY appointment_time
        ''', (target_date,))
        appointments = cursor.fetchall()
        conn.close()

        return appointments, target_date
    except ValueError:
        return None, None


def get_all_appointments():
    """Получает все активные записи (для админа)"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, client_name, appointment_date, appointment_time, service, telegram_user_id
        FROM appointments 
        WHERE status = 'active'
        ORDER BY appointment_date, appointment_time
    ''')
    appointments = cursor.fetchall()
    conn.close()
    return appointments


def get_stats_summary():
    """Получает общую статистику записей"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    week_start = today
    week_end = today + timedelta(days=7)

    # Записи на сегодня
    cursor.execute('SELECT COUNT(*) FROM appointments WHERE appointment_date = ? AND status = "active"', (today,))
    today_count = cursor.fetchone()[0]

    # Записи на завтра
    cursor.execute('SELECT COUNT(*) FROM appointments WHERE appointment_date = ? AND status = "active"', (tomorrow,))
    tomorrow_count = cursor.fetchone()[0]

    # Записи на неделю
    cursor.execute('SELECT COUNT(*) FROM appointments WHERE appointment_date BETWEEN ? AND ? AND status = "active"',
                   (week_start, week_end))
    week_count = cursor.fetchone()[0]

    # Общее количество записей
    cursor.execute('SELECT COUNT(*) FROM appointments WHERE status = "active"')
    total_count = cursor.fetchone()[0]

    # Количество клиентов
    cursor.execute('SELECT COUNT(*) FROM clients')
    clients_count = cursor.fetchone()[0]

    conn.close()

    return {
        'today': today_count,
        'tomorrow': tomorrow_count,
        'week': week_count,
        'total': total_count,
        'clients': clients_count
    }


# ===== ФУНКЦИИ ДЛЯ КЛИЕНТОВ =====

def get_client_appointments(telegram_user_id, include_past=False):
    """Получает записи конкретного клиента"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Проверяем, есть ли колонка telegram_user_id
    cursor.execute("PRAGMA table_info(appointments)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'telegram_user_id' not in columns:
        # Если колонки нет, возвращаем пустой список
        conn.close()
        return []

    if include_past:
        cursor.execute('''
            SELECT id, client_name, appointment_date, appointment_time, service, 
                   COALESCE(status, 'active') as status
            FROM appointments 
            WHERE telegram_user_id = ?
            ORDER BY appointment_date DESC, appointment_time DESC
        ''', (telegram_user_id,))
    else:
        today = datetime.now().date()
        cursor.execute('''
            SELECT id, client_name, appointment_date, appointment_time, service,
                   COALESCE(status, 'active') as status
            FROM appointments 
            WHERE telegram_user_id = ? AND appointment_date >= ? 
            AND COALESCE(status, 'active') = 'active'
            ORDER BY appointment_date, appointment_time
        ''', (telegram_user_id, today))

    appointments = cursor.fetchall()
    conn.close()
    return appointments


def get_available_times(date_str, exclude_appointment_id=None):
    """Получает доступное время на указанную дату"""
    try:
        target_date = datetime.strptime(date_str, '%d.%m.%Y').date()

        # Получаем занятое время
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        if exclude_appointment_id:
            cursor.execute('''
                SELECT appointment_time FROM appointments 
                WHERE appointment_date = ? AND status = 'active' AND id != ?
            ''', (target_date, exclude_appointment_id))
        else:
            cursor.execute('''
                SELECT appointment_time FROM appointments 
                WHERE appointment_date = ? AND status = 'active'
            ''', (target_date,))

        busy_times = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Генерируем доступное время
        available_times = []
        start_hour, start_minute = map(int, WORKING_HOURS['start'].split(':'))
        end_hour, end_minute = map(int, WORKING_HOURS['end'].split(':'))
        break_start_hour, break_start_minute = map(int, WORKING_HOURS['break_start'].split(':'))
        break_end_hour, break_end_minute = map(int, WORKING_HOURS['break_end'].split(':'))

        current_time = datetime.combine(target_date, datetime.min.time().replace(hour=start_hour, minute=start_minute))
        end_time = datetime.combine(target_date, datetime.min.time().replace(hour=end_hour, minute=end_minute))
        break_start = datetime.combine(target_date,
                                       datetime.min.time().replace(hour=break_start_hour, minute=break_start_minute))
        break_end = datetime.combine(target_date,
                                     datetime.min.time().replace(hour=break_end_hour, minute=break_end_minute))

        while current_time < end_time:
            time_str = current_time.strftime('%H:%M')

            # Пропускаем время обеда
            if break_start <= current_time < break_end:
                current_time += timedelta(minutes=30)
                continue

            # Проверяем, не занято ли время
            if time_str not in busy_times:
                available_times.append(time_str)

            current_time += timedelta(minutes=30)

        return available_times

    except ValueError:
        return []


def register_or_update_client(telegram_user_id, name, phone=None):
    """Регистрирует или обновляет информацию о клиенте"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Проверяем, есть ли уже такой клиент
    cursor.execute('SELECT id FROM clients WHERE telegram_user_id = ?', (telegram_user_id,))
    existing_client = cursor.fetchone()

    if existing_client:
        # Обновляем существующего клиента
        cursor.execute('''
            UPDATE clients SET name = ?, phone = ?, last_visit = ?
            WHERE telegram_user_id = ?
        ''', (name, phone, datetime.now().date(), telegram_user_id))
    else:
        # Создаем нового клиента
        cursor.execute('''
            INSERT INTO clients (telegram_user_id, name, phone, first_visit, last_visit)
            VALUES (?, ?, ?, ?, ?)
        ''', (telegram_user_id, name, phone, datetime.now().date(), datetime.now().date()))

    conn.commit()
    conn.close()


def book_appointment(telegram_user_id, client_name, appointment_date, appointment_time, service, phone=None):
    """Создает новую запись для клиента"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Добавляем запись
    cursor.execute('''
        INSERT INTO appointments (client_name, telegram_user_id, phone, appointment_date, appointment_time, service)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (client_name, telegram_user_id, phone, appointment_date, appointment_time, service))

    appointment_id = cursor.lastrowid

    # Обновляем информацию о клиенте
    register_or_update_client(telegram_user_id, client_name, phone)

    # Увеличиваем счетчик визитов
    cursor.execute('''
        UPDATE clients SET total_visits = total_visits + 1
        WHERE telegram_user_id = ?
    ''', (telegram_user_id,))

    conn.commit()
    conn.close()

    return appointment_id


def cancel_appointment_by_client(appointment_id, telegram_user_id):
    """Отменяет запись клиента"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Проверяем, принадлежит ли запись клиенту
    cursor.execute('''
        SELECT id FROM appointments 
        WHERE id = ? AND telegram_user_id = ? AND status = 'active'
    ''', (appointment_id, telegram_user_id))

    if cursor.fetchone():
        cursor.execute('''
            UPDATE appointments SET status = 'cancelled_by_client'
            WHERE id = ?
        ''', (appointment_id,))
        conn.commit()
        conn.close()
        return True

    conn.close()
    return False


def reschedule_appointment(appointment_id, new_date, new_time, telegram_user_id=None):
    """Переносит запись на новое время"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    if telegram_user_id:
        # Клиент может переносить только свои записи
        cursor.execute('''
            UPDATE appointments 
            SET appointment_date = ?, appointment_time = ?, updated_at = ?
            WHERE id = ? AND telegram_user_id = ? AND status = 'active'
        ''', (new_date, new_time, datetime.now(), appointment_id, telegram_user_id))
    else:
        # Админ может переносить любые записи
        cursor.execute('''
            UPDATE appointments 
            SET appointment_date = ?, appointment_time = ?, updated_at = ?
            WHERE id = ? AND status = 'active'
        ''', (new_date, new_time, datetime.now(), appointment_id))

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


# ===== ОБЩИЕ ФУНКЦИИ =====

def add_appointment(client_name, appointment_date, appointment_time, service, telegram_user_id=None, phone=None):
    """Добавление новой записи (универсальная функция)"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO appointments (client_name, telegram_user_id, phone, appointment_date, appointment_time, service)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (client_name, telegram_user_id, phone, appointment_date, appointment_time, service))
    appointment_id = cursor.lastrowid

    # Если есть telegram_user_id, обновляем информацию о клиенте
    if telegram_user_id:
        register_or_update_client(telegram_user_id, client_name, phone)

    conn.commit()
    conn.close()
    return appointment_id


def search_appointment(search_term):
    """Поиск записи по ID, имени клиента или времени"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    if search_term.isdigit():
        # Поиск по ID
        cursor.execute('''
            SELECT id, client_name, appointment_date, appointment_time, service 
            FROM appointments WHERE id = ? AND status = 'active'
        ''', (search_term,))
    else:
        # Поиск по имени или времени
        cursor.execute('''
            SELECT id, client_name, appointment_date, appointment_time, service 
            FROM appointments 
            WHERE (client_name LIKE ? OR appointment_time LIKE ?) AND status = 'active'
        ''', (f'%{search_term}%', f'%{search_term}%'))

    appointments = cursor.fetchall()
    conn.close()
    return appointments


def delete_appointment(appointment_id):
    """Удаление записи по ID (помечает как удаленную)"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE appointments SET status = 'deleted' 
        WHERE id = ?
    ''', (appointment_id,))
    conn.commit()
    conn.close()


def update_appointment_time(appointment_id, new_time):
    """Обновление времени записи"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE appointments SET appointment_time = ?, updated_at = ? 
        WHERE id = ? AND status = 'active'
    ''', (new_time, datetime.now(), appointment_id))
    conn.commit()
    conn.close()


def update_appointment_client(appointment_id, new_client_name):
    """Обновление имени клиента"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE appointments SET client_name = ?, updated_at = ? 
        WHERE id = ? AND status = 'active'
    ''', (new_client_name, datetime.now(), appointment_id))
    conn.commit()
    conn.close()


def update_appointment_service(appointment_id, new_service):
    """Обновление услуги"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE appointments SET service = ?, updated_at = ? 
        WHERE id = ? AND status = 'active'
    ''', (new_service, datetime.now(), appointment_id))
    conn.commit()
    conn.close()


def check_time_conflict(new_time, appointment_date, exclude_id=None):
    """Проверка конфликта времени на определенную дату"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    if exclude_id:
        cursor.execute('''
            SELECT client_name FROM appointments 
            WHERE appointment_time = ? AND appointment_date = ? AND id != ? AND status = 'active'
        ''', (new_time, appointment_date, exclude_id))
    else:
        cursor.execute('''
            SELECT client_name FROM appointments 
            WHERE appointment_time = ? AND appointment_date = ? AND status = 'active'
        ''', (new_time, appointment_date))

    conflict = cursor.fetchone()
    conn.close()
    return conflict


def get_appointment_by_id(appointment_id):
    """Получение информации о записи по ID"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Проверяем, есть ли новые колонки
    cursor.execute("PRAGMA table_info(appointments)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'telegram_user_id' in columns and 'status' in columns:
        cursor.execute('''
            SELECT client_name, appointment_date, appointment_time, service, 
                   COALESCE(telegram_user_id, 0) as telegram_user_id
            FROM appointments 
            WHERE id = ? AND COALESCE(status, 'active') = 'active'
        ''', (appointment_id,))
    else:
        cursor.execute('''
            SELECT client_name, appointment_date, appointment_time, service, 0
            FROM appointments WHERE id = ?
        ''', (appointment_id,))

    appointment = cursor.fetchone()
    conn.close()
    return appointment


def get_client_info(telegram_user_id):
    """Получает информацию о клиенте"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT name, phone, first_visit, total_visits
        FROM clients WHERE telegram_user_id = ?
    ''', (telegram_user_id,))
    client = cursor.fetchone()
    conn.close()
    return client


def get_appointments_count_by_date(date_str):
    """Получает количество записей на конкретную дату"""
    try:
        target_date = datetime.strptime(date_str, '%d.%m.%Y').date()
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM appointments 
            WHERE appointment_date = ? AND status = 'active'
        ''', (target_date,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except ValueError:
        return 0


# Инициализируем базу данных при импорте модуля
init_database()