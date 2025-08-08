import sqlite3
import os
from datetime import datetime, timedelta
from config import DATABASE_PATH, WORKING_HOURS, SERVICES


def init_database():
    """Инициализация базы данных с правильной структурой"""
    # Создаем директорию для БД если её нет
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Включаем поддержку внешних ключей
    cursor.execute("PRAGMA foreign_keys = ON")

    try:
        # Создаем таблицу клиентов
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Создаем таблицу записей с правильными связями
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                telegram_user_id INTEGER,
                phone TEXT,
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                service TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_user_id) REFERENCES clients (telegram_user_id)
            )
        ''')

        # Создаем индексы для быстрого поиска
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointment_date ON appointments(appointment_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_telegram_user_id ON appointments(telegram_user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointment_status ON appointments(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_client_telegram_id ON clients(telegram_user_id)')

        # Создаем триггер для обновления updated_at
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_appointments_timestamp 
            AFTER UPDATE ON appointments
            FOR EACH ROW
            BEGIN
                UPDATE appointments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        ''')

        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_clients_timestamp 
            AFTER UPDATE ON clients
            FOR EACH ROW
            BEGIN
                UPDATE clients SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        ''')

        conn.commit()
        print("✅ База данных успешно инициализирована")

        # Проверяем структуру таблиц
        cursor.execute("PRAGMA table_info(appointments)")
        appointments_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Колонки таблицы appointments: {appointments_columns}")

        cursor.execute("PRAGMA table_info(clients)")
        clients_columns = [column[1] for column in cursor.fetchall()]
        print(f"👥 Колонки таблицы clients: {clients_columns}")

    except sqlite3.Error as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        conn.rollback()
    finally:
        conn.close()


def check_database_integrity():
    """Проверка целостности базы данных"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Проверяем целостность
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()

        if result[0] == "ok":
            print("✅ Целостность БД в порядке")
            return True
        else:
            print(f"❌ Проблемы с целостностью БД: {result[0]}")
            return False

    except sqlite3.Error as e:
        print(f"❌ Ошибка проверки БД: {e}")
        return False
    finally:
        conn.close()


# ===== ФУНКЦИИ ДЛЯ АДМИНИСТРАТОРА =====

def get_schedule_by_date(date_offset=0):
    """Получает расписание на определенную дату (для админа)"""
    target_date = datetime.now().date() + timedelta(days=date_offset)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT client_name, appointment_time, service 
            FROM appointments 
            WHERE appointment_date = ? AND status = 'active'
            ORDER BY appointment_time
        ''', (target_date,))
        appointments = cursor.fetchall()
        return appointments, target_date

    except sqlite3.Error as e:
        print(f"❌ Ошибка получения расписания: {e}")
        return [], target_date
    finally:
        conn.close()


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

        return appointments, target_date

    except (ValueError, sqlite3.Error) as e:
        print(f"❌ Ошибка получения расписания по дате: {e}")
        return None, None
    finally:
        if 'conn' in locals():
            conn.close()


def get_all_appointments():
    """Получает все активные записи (для админа)"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT id, client_name, appointment_date, appointment_time, service, 
                   COALESCE(telegram_user_id, 0) as telegram_user_id
            FROM appointments 
            WHERE status = 'active'
            ORDER BY appointment_date, appointment_time
        ''')
        appointments = cursor.fetchall()
        return appointments

    except sqlite3.Error as e:
        print(f"❌ Ошибка получения всех записей: {e}")
        return []
    finally:
        conn.close()


def get_stats_summary():
    """Получает общую статистику записей"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    week_start = today
    week_end = today + timedelta(days=7)

    try:
        # Записи на сегодня
        cursor.execute('SELECT COUNT(*) FROM appointments WHERE appointment_date = ? AND status = "active"', (today,))
        today_count = cursor.fetchone()[0]

        # Записи на завтра
        cursor.execute('SELECT COUNT(*) FROM appointments WHERE appointment_date = ? AND status = "active"',
                       (tomorrow,))
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

        return {
            'today': today_count,
            'tomorrow': tomorrow_count,
            'week': week_count,
            'total': total_count,
            'clients': clients_count
        }

    except sqlite3.Error as e:
        print(f"❌ Ошибка получения статистики: {e}")
        return {
            'today': 0,
            'tomorrow': 0,
            'week': 0,
            'total': 0,
            'clients': 0
        }
    finally:
        conn.close()


# ===== ФУНКЦИИ ДЛЯ КЛИЕНТОВ =====

def get_client_appointments(telegram_user_id, include_past=False):
    """Получает записи конкретного клиента"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
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
        return appointments

    except sqlite3.Error as e:
        print(f"❌ Ошибка получения записей клиента: {e}")
        return []
    finally:
        conn.close()


def get_available_times(date_str, exclude_appointment_id=None):
    """Получает доступное время на указанную дату"""
    try:
        target_date = datetime.strptime(date_str, '%d.%m.%Y').date()

        # Проверяем, что дата не в прошлом
        if target_date < datetime.now().date():
            return []

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

    except (ValueError, sqlite3.Error) as e:
        print(f"❌ Ошибка получения доступного времени: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


def register_or_update_client(telegram_user_id, name, phone=None):
    """Регистрирует или обновляет информацию о клиенте"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
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
        return True

    except sqlite3.Error as e:
        print(f"❌ Ошибка регистрации клиента: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def book_appointment(telegram_user_id, client_name, appointment_date, appointment_time, service, phone=None):
    """Создает новую запись для клиента"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Проверяем конфликт времени
        conflict = check_time_conflict(appointment_time, appointment_date)
        if conflict:
            print(f"⚠️ Конфликт времени: {appointment_time} уже занято")
            return None

        # Добавляем запись
        cursor.execute('''
            INSERT INTO appointments (client_name, telegram_user_id, phone, appointment_date, appointment_time, service, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
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
        return appointment_id

    except sqlite3.Error as e:
        print(f"❌ Ошибка создания записи: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def cancel_appointment_by_client(appointment_id, telegram_user_id):
    """Отменяет запись клиента"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
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
            return True

        return False

    except sqlite3.Error as e:
        print(f"❌ Ошибка отмены записи: {e}")
        return False
    finally:
        conn.close()


def reschedule_appointment(appointment_id, new_date, new_time, telegram_user_id=None):
    """Переносит запись на новое время"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Проверяем конфликт времени (исключая текущую запись)
        conflict = check_time_conflict(new_time, new_date, appointment_id)
        if conflict:
            print(f"⚠️ Конфликт времени при переносе: {new_time} уже занято")
            return False

        if telegram_user_id:
            # Клиент может переносить только свои записи
            cursor.execute('''
                UPDATE appointments 
                SET appointment_date = ?, appointment_time = ?
                WHERE id = ? AND telegram_user_id = ? AND status = 'active'
            ''', (new_date, new_time, appointment_id, telegram_user_id))
        else:
            # Админ может переносить любые записи
            cursor.execute('''
                UPDATE appointments 
                SET appointment_date = ?, appointment_time = ?
                WHERE id = ? AND status = 'active'
            ''', (new_date, new_time, appointment_id))

        success = cursor.rowcount > 0
        conn.commit()
        return success

    except sqlite3.Error as e:
        print(f"❌ Ошибка переноса записи: {e}")
        return False
    finally:
        conn.close()


# ===== ОБЩИЕ ФУНКЦИИ =====

def add_appointment(client_name, appointment_date, appointment_time, service, telegram_user_id=None, phone=None):
    """Добавление новой записи (универсальная функция)"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        # Проверяем конфликт времени
        conflict = check_time_conflict(appointment_time, appointment_date)
        if conflict:
            print(f"⚠️ Конфликт времени: {appointment_time} уже занято клиентом {conflict[0]}")
            return None

        cursor.execute('''
            INSERT INTO appointments (client_name, telegram_user_id, phone, appointment_date, appointment_time, service, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
        ''', (client_name, telegram_user_id, phone, appointment_date, appointment_time, service))

        appointment_id = cursor.lastrowid

        # Если есть telegram_user_id, обновляем информацию о клиенте
        if telegram_user_id:
            register_or_update_client(telegram_user_id, client_name, phone)

        conn.commit()
        return appointment_id

    except sqlite3.Error as e:
        print(f"❌ Ошибка добавления записи: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def search_appointment(search_term):
    """Поиск записи по ID, имени клиента или времени"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
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
                ORDER BY appointment_date, appointment_time
            ''', (f'%{search_term}%', f'%{search_term}%'))

        appointments = cursor.fetchall()
        return appointments

    except sqlite3.Error as e:
        print(f"❌ Ошибка поиска записи: {e}")
        return []
    finally:
        conn.close()


def delete_appointment(appointment_id):
    """Удаление записи по ID (помечает как удаленную)"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE appointments SET status = 'deleted' 
            WHERE id = ? AND status = 'active'
        ''', (appointment_id,))

        success = cursor.rowcount > 0
        conn.commit()
        return success

    except sqlite3.Error as e:
        print(f"❌ Ошибка удаления записи: {e}")
        return False
    finally:
        conn.close()


def update_appointment_time(appointment_id, new_time):
    """Обновление времени записи"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE appointments SET appointment_time = ? 
            WHERE id = ? AND status = 'active'
        ''', (new_time, appointment_id))

        success = cursor.rowcount > 0
        conn.commit()
        return success

    except sqlite3.Error as e:
        print(f"❌ Ошибка обновления времени: {e}")
        return False
    finally:
        conn.close()


def update_appointment_client(appointment_id, new_client_name):
    """Обновление имени клиента"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE appointments SET client_name = ? 
            WHERE id = ? AND status = 'active'
        ''', (new_client_name, appointment_id))

        success = cursor.rowcount > 0
        conn.commit()
        return success

    except sqlite3.Error as e:
        print(f"❌ Ошибка обновления клиента: {e}")
        return False
    finally:
        conn.close()


def update_appointment_service(appointment_id, new_service):
    """Обновление услуги"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE appointments SET service = ? 
            WHERE id = ? AND status = 'active'
        ''', (new_service, appointment_id))

        success = cursor.rowcount > 0
        conn.commit()
        return success

    except sqlite3.Error as e:
        print(f"❌ Ошибка обновления услуги: {e}")
        return False
    finally:
        conn.close()


def check_time_conflict(new_time, appointment_date, exclude_id=None):
    """Проверка конфликта времени на определенную дату"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
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
        return conflict

    except sqlite3.Error as e:
        print(f"❌ Ошибка проверки конфликта: {e}")
        return None
    finally:
        conn.close()


def get_appointment_by_id(appointment_id):
    """Получение информации о записи по ID"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT client_name, appointment_date, appointment_time, service, 
                   COALESCE(telegram_user_id, 0) as telegram_user_id
            FROM appointments 
            WHERE id = ? AND status = 'active'
        ''', (appointment_id,))

        appointment = cursor.fetchone()
        return appointment

    except sqlite3.Error as e:
        print(f"❌ Ошибка получения записи по ID: {e}")
        return None
    finally:
        conn.close()


def get_client_info(telegram_user_id):
    """Получает информацию о клиенте"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT name, phone, first_visit, total_visits, notes
            FROM clients WHERE telegram_user_id = ?
        ''', (telegram_user_id,))

        client = cursor.fetchone()
        return client

    except sqlite3.Error as e:
        print(f"❌ Ошибка получения информации о клиенте: {e}")
        return None
    finally:
        conn.close()


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
        return count

    except (ValueError, sqlite3.Error) as e:
        print(f"❌ Ошибка подсчета записей: {e}")
        return 0
    finally:
        if 'conn' in locals():
            conn.close()


def cleanup_old_appointments(days_old=30):
    """Очистка старых записей (старше указанного количества дней)"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cutoff_date = datetime.now().date() - timedelta(days=days_old)

        cursor.execute('''
            UPDATE appointments SET status = 'archived'
            WHERE appointment_date < ? AND status IN ('cancelled_by_client', 'deleted')
        ''', (cutoff_date,))

        archived_count = cursor.rowcount
        conn.commit()

        print(f"📋 Архивировано {archived_count} старых записей")
        return archived_count

    except sqlite3.Error as e:
        print(f"❌ Ошибка очистки записей: {e}")
        return 0
    finally:
        conn.close()


def get_database_info():
    """Получает информацию о базе данных"""
    if not os.path.exists(DATABASE_PATH):
        return "❌ База данных не найдена"

    size = os.path.getsize(DATABASE_PATH)
    size_mb = size / (1024 * 1024)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM appointments WHERE status = 'active'")
        active_appointments = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM appointments")
        total_appointments = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM clients")
        total_clients = cursor.fetchone()[0]

        return f"""📊 Информация о базе данных:
📁 Размер: {size_mb:.2f} MB
📋 Активных записей: {active_appointments}
📝 Всего записей: {total_appointments}
👥 Клиентов: {total_clients}
💾 Путь: {DATABASE_PATH}"""

    except sqlite3.Error as e:
        return f"❌ Ошибка получения информации: {e}"
    finally:
        conn.close()


# Инициализируем базу данных при импорте модуля
if __name__ == "__main__":
    init_database()
    check_database_integrity()
    print(get_database_info())
else:
    init_database()