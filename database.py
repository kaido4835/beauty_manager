import sqlite3
from datetime import datetime, timedelta
from config import DATABASE_PATH


def get_schedule_by_date(date_offset=0):
    """Получает расписание на определенную дату"""
    target_date = datetime.now().date() + timedelta(days=date_offset)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT client_name, appointment_time, service 
        FROM appointments 
        WHERE appointment_date = ? 
        ORDER BY appointment_time
    ''', (target_date,))
    appointments = cursor.fetchall()
    conn.close()

    return appointments, target_date


def get_schedule():
    """Получает расписание на сегодня"""
    appointments, _ = get_schedule_by_date(0)
    return appointments


def get_schedule_by_specific_date(date_str):
    """Получает расписание на конкретную дату"""
    try:
        target_date = datetime.strptime(date_str, '%d.%m.%Y').date()

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Получаем расписание с ID для возможности редактирования
        cursor.execute('''
            SELECT id, client_name, appointment_time, service 
            FROM appointments 
            WHERE appointment_date = ? 
            ORDER BY appointment_time
        ''', (target_date,))
        appointments = cursor.fetchall()
        conn.close()

        return appointments, target_date
    except ValueError:
        return None, None


def get_stats_summary():
    """Получает общую статистику записей"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    week_start = today
    week_end = today + timedelta(days=7)

    # Записи на сегодня
    cursor.execute('SELECT COUNT(*) FROM appointments WHERE appointment_date = ?', (today,))
    today_count = cursor.fetchone()[0]

    # Записи на завтра
    cursor.execute('SELECT COUNT(*) FROM appointments WHERE appointment_date = ?', (tomorrow,))
    tomorrow_count = cursor.fetchone()[0]

    # Записи на неделю
    cursor.execute('SELECT COUNT(*) FROM appointments WHERE appointment_date BETWEEN ? AND ?', (week_start, week_end))
    week_count = cursor.fetchone()[0]

    # Общее количество записей
    cursor.execute('SELECT COUNT(*) FROM appointments')
    total_count = cursor.fetchone()[0]

    conn.close()

    return {
        'today': today_count,
        'tomorrow': tomorrow_count,
        'week': week_count,
        'total': total_count
    }


def add_appointment(client_name, appointment_date, appointment_time, service):
    """Добавление новой записи"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO appointments (client_name, appointment_date, appointment_time, service)
        VALUES (?, ?, ?, ?)
    ''', (client_name, appointment_date, appointment_time, service))
    appointment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return appointment_id


def get_appointments_count_by_date(date_str):
    """Получает количество записей на конкретную дату"""
    try:
        target_date = datetime.strptime(date_str, '%d.%m.%Y').date()

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM appointments 
            WHERE appointment_date = ?
        ''', (target_date,))
        count = cursor.fetchone()[0]
        conn.close()

        return count
    except ValueError:
        return 0


def search_appointment(search_term):
    """Поиск записи по ID, имени клиента или времени"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    if search_term.isdigit():
        # Поиск по ID
        cursor.execute('''
            SELECT id, client_name, appointment_date, appointment_time, service 
            FROM appointments WHERE id = ?
        ''', (search_term,))
    else:
        # Поиск по имени или времени
        cursor.execute('''
            SELECT id, client_name, appointment_date, appointment_time, service 
            FROM appointments 
            WHERE client_name LIKE ? OR appointment_time LIKE ?
        ''', (f'%{search_term}%', f'%{search_term}%'))

    appointments = cursor.fetchall()
    conn.close()
    return appointments


def delete_appointment(appointment_id):
    """Удаление записи по ID"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
    conn.commit()
    conn.close()


def update_appointment_time(appointment_id, new_time):
    """Обновление времени записи"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE appointments SET appointment_time = ? WHERE id = ?', (new_time, appointment_id))
    conn.commit()
    conn.close()


def check_time_conflict(new_time, appointment_date, exclude_id=None):
    """Проверка конфликта времени на определенную дату"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    if exclude_id:
        cursor.execute('''
            SELECT client_name FROM appointments 
            WHERE appointment_time = ? AND appointment_date = ? AND id != ?
        ''', (new_time, appointment_date, exclude_id))
    else:
        cursor.execute('''
            SELECT client_name FROM appointments 
            WHERE appointment_time = ? AND appointment_date = ?
        ''', (new_time, appointment_date))

    conflict = cursor.fetchone()
    conn.close()
    return conflict


def get_appointment_by_id(appointment_id):
    """Получение информации о записи по ID"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT client_name, appointment_date, appointment_time, service 
        FROM appointments WHERE id = ?
    ''', (appointment_id,))
    appointment = cursor.fetchone()
    conn.close()
    return appointment