import sqlite3
import os
import threading
from datetime import datetime, timedelta
from config import DATABASE_PATH, WORKING_HOURS, SERVICES

# Thread-safe database connection
_thread_local = threading.local()


def get_connection():
    """Получает thread-safe соединение с базой данных"""
    if not hasattr(_thread_local, 'connection'):
        _thread_local.connection = sqlite3.connect(DATABASE_PATH, timeout=30.0)
        _thread_local.connection.execute("PRAGMA journal_mode=WAL")
        _thread_local.connection.execute("PRAGMA foreign_keys=ON")
        _thread_local.connection.execute("PRAGMA busy_timeout=30000")
    return _thread_local.connection


def close_connection():
    """Закрывает соединение для текущего потока"""
    if hasattr(_thread_local, 'connection'):
        _thread_local.connection.close()
        delattr(_thread_local, 'connection')


def safe_execute(query, params=(), fetch_type='none'):
    """Безопасное выполнение SQL запросов"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query, params)

        if fetch_type == 'one':
            result = cursor.fetchone()
        elif fetch_type == 'all':
            result = cursor.fetchall()
        elif fetch_type == 'lastrowid':
            result = cursor.lastrowid
        elif fetch_type == 'rowcount':
            result = cursor.rowcount
        else:
            result = None

        conn.commit()
        return result

    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Ошибка выполнения запроса: {e}")
        print(f"SQL: {query}")
        print(f"Params: {params}")
        return None


def init_database():
    """Инициализация базы данных с правильной структурой"""
    # Создаем директорию для БД если её нет
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Включаем WAL mode для лучшей производительности
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=30000")

        # Проверяем существующую структуру таблиц
        cursor.execute("PRAGMA table_info(appointments)")
        existing_columns = [column[1] for column in cursor.fetchall()]

        if not existing_columns:
            # Таблица не существует - создаем с нуля
            print("📋 Создание новой таблицы appointments...")
            cursor.execute('''
                CREATE TABLE appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_name TEXT NOT NULL,
                    telegram_user_id INTEGER,
                    phone TEXT,
                    appointment_date DATE NOT NULL,
                    appointment_time TIME NOT NULL,
                    service TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            # Таблица существует - проверяем и добавляем недостающие колонки
            print(f"📋 Существующие колонки: {existing_columns}")

            # Добавляем недостающие колонки если их нет
            if 'created_at' not in existing_columns:
                print("➕ Добавляем колонку created_at")
                cursor.execute('ALTER TABLE appointments ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')

            if 'status' not in existing_columns:
                print("➕ Добавляем колонку status")
                cursor.execute('ALTER TABLE appointments ADD COLUMN status TEXT DEFAULT "active"')

            if 'telegram_user_id' not in existing_columns:
                print("➕ Добавляем колонку telegram_user_id")
                cursor.execute('ALTER TABLE appointments ADD COLUMN telegram_user_id INTEGER')

        # Создаем таблицу клиентов (упрощенная версия)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER UNIQUE NOT NULL,
                name TEXT,
                phone TEXT,
                first_visit DATE,
                last_visit DATE,
                total_visits INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Создаем индексы
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointment_date ON appointments(appointment_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_telegram_user_id ON appointments(telegram_user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointment_status ON appointments(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_telegram_id ON clients(telegram_user_id)')

        conn.commit()
        print("✅ База данных успешно инициализирована")

        # Обновляем статус для старых записей без статуса
        cursor.execute("UPDATE appointments SET status = 'active' WHERE status IS NULL OR status = ''")
        updated = cursor.rowcount
        if updated > 0:
            print(f"📝 Обновлено {updated} записей со статусом")
            conn.commit()

    except sqlite3.Error as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()


def check_database_integrity():
    """Проверка целостности базы данных"""
    try:
        result = safe_execute("PRAGMA integrity_check", fetch_type='one')
        if result and result[0] == "ok":
            print("✅ Целостность БД в порядке")
            return True
        else:
            print(f"❌ Проблемы с целостностью БД: {result}")
            return False
    except Exception as e:
        print(f"❌ Ошибка проверки БД: {e}")
        return False


# ===== ФУНКЦИИ ДЛЯ АДМИНИСТРАТОРА =====

def get_schedule_by_date(date_offset=0):
    """Получает расписание на определенную дату (для админа)"""
    target_date = datetime.now().date() + timedelta(days=date_offset)

    appointments = safe_execute('''
        SELECT client_name, appointment_time, service 
        FROM appointments 
        WHERE appointment_date = ? AND status = 'active'
        ORDER BY appointment_time
    ''', (target_date,), 'all')

    if appointments is None:
        appointments = []

    return appointments, target_date


def get_schedule_by_specific_date(date_str):
    """Получает расписание на конкретную дату (для админа)"""
    try:
        target_date = datetime.strptime(date_str, '%d.%m.%Y').date()

        appointments = safe_execute('''
            SELECT id, client_name, appointment_time, service 
            FROM appointments 
            WHERE appointment_date = ? AND status = 'active'
            ORDER BY appointment_time
        ''', (target_date,), 'all')

        if appointments is None:
            appointments = []

        return appointments, target_date

    except ValueError as e:
        print(f"❌ Ошибка парсинга даты: {e}")
        return None, None


def get_stats_summary():
    """Получает общую статистику записей"""
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    week_start = today
    week_end = today + timedelta(days=7)

    # Записи на сегодня
    today_count = safe_execute(
        'SELECT COUNT(*) FROM appointments WHERE appointment_date = ? AND status = "active"',
        (today,), 'one'
    )
    today_count = today_count[0] if today_count else 0

    # Записи на завтра
    tomorrow_count = safe_execute(
        'SELECT COUNT(*) FROM appointments WHERE appointment_date = ? AND status = "active"',
        (tomorrow,), 'one'
    )
    tomorrow_count = tomorrow_count[0] if tomorrow_count else 0

    # Записи на неделю
    week_count = safe_execute(
        'SELECT COUNT(*) FROM appointments WHERE appointment_date BETWEEN ? AND ? AND status = "active"',
        (week_start, week_end), 'one'
    )
    week_count = week_count[0] if week_count else 0

    # Общее количество записей
    total_count = safe_execute('SELECT COUNT(*) FROM appointments WHERE status = "active"', fetch_type='one')
    total_count = total_count[0] if total_count else 0

    # Количество клиентов
    clients_count = safe_execute('SELECT COUNT(*) FROM clients', fetch_type='one')
    clients_count = clients_count[0] if clients_count else 0

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
    if include_past:
        appointments = safe_execute('''
            SELECT id, client_name, appointment_date, appointment_time, service, 
                   COALESCE(status, 'active') as status
            FROM appointments 
            WHERE telegram_user_id = ?
            ORDER BY appointment_date DESC, appointment_time DESC
        ''', (telegram_user_id,), 'all')
    else:
        today = datetime.now().date()
        appointments = safe_execute('''
            SELECT id, client_name, appointment_date, appointment_time, service,
                   COALESCE(status, 'active') as status
            FROM appointments 
            WHERE telegram_user_id = ? AND appointment_date >= ? 
            AND COALESCE(status, 'active') = 'active'
            ORDER BY appointment_date, appointment_time
        ''', (telegram_user_id, today), 'all')

    return appointments if appointments is not None else []


def get_available_times(date_str, exclude_appointment_id=None):
    """Получает доступное время на указанную дату"""
    try:
        target_date = datetime.strptime(date_str, '%d.%m.%Y').date()

        # Проверяем, что дата не в прошлом
        if target_date < datetime.now().date():
            return []

        # Получаем занятое время
        if exclude_appointment_id:
            busy_times_result = safe_execute('''
                SELECT appointment_time FROM appointments 
                WHERE appointment_date = ? AND status = 'active' AND id != ?
            ''', (target_date, exclude_appointment_id), 'all')
        else:
            busy_times_result = safe_execute('''
                SELECT appointment_time FROM appointments 
                WHERE appointment_date = ? AND status = 'active'
            ''', (target_date,), 'all')

        busy_times = [row[0] for row in busy_times_result] if busy_times_result else []

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
                # Если это сегодня, проверяем, что время еще не прошло
                if target_date == datetime.now().date():
                    if current_time.time() > datetime.now().time():
                        available_times.append(time_str)
                else:
                    available_times.append(time_str)

            current_time += timedelta(minutes=30)

        return available_times

    except ValueError as e:
        print(f"❌ Ошибка получения доступного времени: {e}")
        return []


def register_or_update_client(telegram_user_id, name, phone=None):
    """Регистрирует или обновляет информацию о клиенте"""
    # Проверяем, есть ли уже такой клиент
    existing_client = safe_execute(
        'SELECT id FROM clients WHERE telegram_user_id = ?',
        (telegram_user_id,), 'one'
    )

    if existing_client:
        # Обновляем существующего клиента
        result = safe_execute('''
            UPDATE clients SET name = ?, phone = ?, last_visit = ?
            WHERE telegram_user_id = ?
        ''', (name, phone, datetime.now().date(), telegram_user_id), 'rowcount')
        return result is not None
    else:
        # Создаем нового клиента
        result = safe_execute('''
            INSERT INTO clients (telegram_user_id, name, phone, first_visit, last_visit)
            VALUES (?, ?, ?, ?, ?)
        ''', (telegram_user_id, name, phone, datetime.now().date(), datetime.now().date()), 'lastrowid')
        return result is not None


def book_appointment(telegram_user_id, client_name, appointment_date, appointment_time, service, phone=None):
    """Создает новую запись для клиента"""
    # Проверяем конфликт времени
    conflict = check_time_conflict(appointment_time, appointment_date)
    if conflict:
        print(f"⚠️ Конфликт времени: {appointment_time} уже занято")
        return None

    # Добавляем запись
    appointment_id = safe_execute('''
        INSERT INTO appointments (client_name, telegram_user_id, phone, appointment_date, appointment_time, service, status)
        VALUES (?, ?, ?, ?, ?, ?, 'active')
    ''', (client_name, telegram_user_id, phone, appointment_date, appointment_time, service), 'lastrowid')

    if appointment_id:
        # Обновляем информацию о клиенте
        register_or_update_client(telegram_user_id, client_name, phone)

        # Увеличиваем счетчик визитов
        safe_execute('''
            UPDATE clients SET total_visits = total_visits + 1
            WHERE telegram_user_id = ?
        ''', (telegram_user_id,))

    return appointment_id


def cancel_appointment_by_client(appointment_id, telegram_user_id):
    """Отменяет запись клиента"""
    # Проверяем, принадлежит ли запись клиенту
    appointment = safe_execute('''
        SELECT id FROM appointments 
        WHERE id = ? AND telegram_user_id = ? AND status = 'active'
    ''', (appointment_id, telegram_user_id), 'one')

    if appointment:
        result = safe_execute('''
            UPDATE appointments SET status = 'cancelled_by_client'
            WHERE id = ?
        ''', (appointment_id,), 'rowcount')
        return result is not None and result > 0

    return False


def reschedule_appointment(appointment_id, new_date, new_time, telegram_user_id=None):
    """Переносит запись на новое время"""
    # Проверяем конфликт времени (исключая текущую запись)
    conflict = check_time_conflict(new_time, new_date, appointment_id)
    if conflict:
        print(f"⚠️ Конфликт времени при переносе: {new_time} уже занято")
        return False

    if telegram_user_id:
        # Клиент может переносить только свои записи
        result = safe_execute('''
            UPDATE appointments 
            SET appointment_date = ?, appointment_time = ?
            WHERE id = ? AND telegram_user_id = ? AND status = 'active'
        ''', (new_date, new_time, appointment_id, telegram_user_id), 'rowcount')
    else:
        # Админ может переносить любые записи
        result = safe_execute('''
            UPDATE appointments 
            SET appointment_date = ?, appointment_time = ?
            WHERE id = ? AND status = 'active'
        ''', (new_date, new_time, appointment_id), 'rowcount')

    return result is not None and result > 0


# ===== ОБЩИЕ ФУНКЦИИ =====

def add_appointment(client_name, appointment_date, appointment_time, service, telegram_user_id=None, phone=None):
    """Добавление новой записи (универсальная функция)"""
    # Проверяем конфликт времени
    conflict = check_time_conflict(appointment_time, appointment_date)
    if conflict:
        print(f"⚠️ Конфликт времени: {appointment_time} уже занято клиентом {conflict[0]}")
        return None

    appointment_id = safe_execute('''
        INSERT INTO appointments (client_name, telegram_user_id, phone, appointment_date, appointment_time, service, status)
        VALUES (?, ?, ?, ?, ?, ?, 'active')
    ''', (client_name, telegram_user_id, phone, appointment_date, appointment_time, service), 'lastrowid')

    # Если есть telegram_user_id, обновляем информацию о клиенте
    if appointment_id and telegram_user_id:
        register_or_update_client(telegram_user_id, client_name, phone)

    return appointment_id


def search_appointment(search_term):
    """Поиск записи по ID, имени клиента или времени"""
    if search_term.isdigit():
        # Поиск по ID
        appointments = safe_execute('''
            SELECT id, client_name, appointment_date, appointment_time, service 
            FROM appointments WHERE id = ? AND status = 'active'
        ''', (search_term,), 'all')
    else:
        # Поиск по имени или времени
        appointments = safe_execute('''
            SELECT id, client_name, appointment_date, appointment_time, service 
            FROM appointments 
            WHERE (client_name LIKE ? OR appointment_time LIKE ?) AND status = 'active'
            ORDER BY appointment_date, appointment_time
        ''', (f'%{search_term}%', f'%{search_term}%'), 'all')

    return appointments if appointments is not None else []


def delete_appointment(appointment_id):
    """Удаление записи по ID (помечает как удаленную)"""
    result = safe_execute('''
        UPDATE appointments SET status = 'deleted' 
        WHERE id = ? AND status = 'active'
    ''', (appointment_id,), 'rowcount')

    return result is not None and result > 0


def update_appointment_time(appointment_id, new_time):
    """Обновление времени записи"""
    result = safe_execute('''
        UPDATE appointments SET appointment_time = ? 
        WHERE id = ? AND status = 'active'
    ''', (new_time, appointment_id), 'rowcount')

    return result is not None and result > 0


def update_appointment_client(appointment_id, new_client_name):
    """Обновление имени клиента"""
    result = safe_execute('''
        UPDATE appointments SET client_name = ? 
        WHERE id = ? AND status = 'active'
    ''', (new_client_name, appointment_id), 'rowcount')

    return result is not None and result > 0


def update_appointment_service(appointment_id, new_service):
    """Обновление услуги"""
    result = safe_execute('''
        UPDATE appointments SET service = ? 
        WHERE id = ? AND status = 'active'
    ''', (new_service, appointment_id), 'rowcount')

    return result is not None and result > 0


def check_time_conflict(new_time, appointment_date, exclude_id=None):
    """Проверка конфликта времени на определенную дату"""
    if exclude_id:
        conflict = safe_execute('''
            SELECT client_name FROM appointments 
            WHERE appointment_time = ? AND appointment_date = ? AND id != ? AND status = 'active'
        ''', (new_time, appointment_date, exclude_id), 'one')
    else:
        conflict = safe_execute('''
            SELECT client_name FROM appointments 
            WHERE appointment_time = ? AND appointment_date = ? AND status = 'active'
        ''', (new_time, appointment_date), 'one')

    return conflict


def get_appointment_by_id(appointment_id):
    """Получение информации о записи по ID"""
    appointment = safe_execute('''
        SELECT client_name, appointment_date, appointment_time, service, 
               COALESCE(telegram_user_id, 0) as telegram_user_id
        FROM appointments 
        WHERE id = ? AND status = 'active'
    ''', (appointment_id,), 'one')

    return appointment


def get_client_info(telegram_user_id):
    """Получает информацию о клиенте"""
    client = safe_execute('''
        SELECT name, phone, first_visit, total_visits, notes
        FROM clients WHERE telegram_user_id = ?
    ''', (telegram_user_id,), 'one')

    return client


def cleanup_old_appointments(days_old=30):
    """Очистка старых записей (старше указанного количества дней)"""
    cutoff_date = datetime.now().date() - timedelta(days=days_old)

    result = safe_execute('''
        UPDATE appointments SET status = 'archived'
        WHERE appointment_date < ? AND status IN ('cancelled_by_client', 'deleted')
    ''', (cutoff_date,), 'rowcount')

    archived_count = result if result is not None else 0
    if archived_count > 0:
        print(f"📋 Архивировано {archived_count} старых записей")

    return archived_count


def get_database_info():
    """Получает информацию о базе данных"""
    if not os.path.exists(DATABASE_PATH):
        return "❌ База данных не найдена"

    size = os.path.getsize(DATABASE_PATH)
    size_mb = size / (1024 * 1024)

    active_appointments = safe_execute(
        "SELECT COUNT(*) FROM appointments WHERE status = 'active'",
        fetch_type='one'
    )
    active_appointments = active_appointments[0] if active_appointments else 0

    total_appointments = safe_execute("SELECT COUNT(*) FROM appointments", fetch_type='one')
    total_appointments = total_appointments[0] if total_appointments else 0

    total_clients = safe_execute("SELECT COUNT(*) FROM clients", fetch_type='one')
    total_clients = total_clients[0] if total_clients else 0

    return f"""📊 Информация о базе данных:
📁 Размер: {size_mb:.2f} MB
📋 Активных записей: {active_appointments}
📝 Всего записей: {total_appointments}
👥 Клиентов: {total_clients}
💾 Путь: {DATABASE_PATH}"""


# Инициализируем базу данных при импорте модуля
if __name__ == "__main__":
    init_database()
    check_database_integrity()
    print(get_database_info())
else:
    init_database()