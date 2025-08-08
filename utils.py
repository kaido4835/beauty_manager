from datetime import datetime
from config import MONTHS, WEEKDAYS


def format_date_russian(date_obj):
    """Форматирование даты на русском языке"""
    day = date_obj.day
    month = MONTHS[date_obj.month]
    weekday = WEEKDAYS[date_obj.weekday()]

    return f"{weekday}, {day} {month}"


def validate_time_format(time_str):
    """Валидация формата времени ЧЧ:ММ"""
    try:
        time_parts = time_str.split(':')
        if len(time_parts) != 2:
            return False

        hours = int(time_parts[0])
        minutes = int(time_parts[1])

        return 0 <= hours <= 23 and 0 <= minutes <= 59
    except ValueError:
        return False


def validate_date_format(date_str):
    """Валидация формата даты ДД.ММ.ГГГГ"""
    try:
        datetime.strptime(date_str, '%d.%m.%Y')
        return True
    except ValueError:
        return False


def format_schedule_text(appointments, target_date):
    """Форматирует текст расписания"""
    date_text = format_date_russian(target_date)

    if appointments:
        # Проверяем формат данных (с ID или без)
        if len(appointments[0]) == 4:  # Формат с ID (id, client_name, appointment_time, service)
            schedule_text = f"📅 Расписание на {date_text}:\n\n"
            for appointment_id, client_name, appointment_time, service in appointments:
                schedule_text += f"🕐 {appointment_time} - {client_name}\n"
                schedule_text += f"📋 Услуга: {service}\n"
                schedule_text += f"🆔 ID: {appointment_id}\n\n"
        else:  # Обычный формат (client_name, appointment_time, service)
            schedule_text = f"📅 Расписание на {date_text}:\n\n"
            for client_name, appointment_time, service in appointments:
                schedule_text += f"🕐 {appointment_time} - {client_name}\n"
                schedule_text += f"📋 Услуга: {service}\n\n"
    else:
        schedule_text = f"📅 На {date_text} записей нет"

    return schedule_text


def format_appointment_info(appointment_id, client_name, appointment_date, appointment_time, service):
    """Форматирует информацию о записи"""
    date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
    formatted_date = format_date_russian(date_obj)

    return (
        f"📝 Найдена запись:\n\n"
        f"🆔 ID: {appointment_id}\n"
        f"👤 Клиент: {client_name}\n"
        f"📅 Дата: {formatted_date}\n"
        f"🕐 Время: {appointment_time}\n"
        f"📋 Услуга: {service}\n\n"
        f"Выберите действие:"
    )


def format_multiple_appointments(appointments):
    """Форматирует список найденных записей"""
    result_text = f"🔍 Найдено {len(appointments)} записей:\n\n"
    for appointment_id, client_name, appointment_date, appointment_time, service in appointments:
        date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        formatted_date = format_date_russian(date_obj)
        result_text += f"🆔 {appointment_id}: {client_name} - {formatted_date} {appointment_time} ({service})\n"

    result_text += "\n📝 Введите точный ID записи для редактирования:"
    return result_text


def format_delete_confirmation(client_name, appointment_date, appointment_time, service):
    """Форматирует сообщение подтверждения удаления"""
    date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
    formatted_date = format_date_russian(date_obj)

    return (
        f"⚠️ Подтвердите удаление записи:\n\n"
        f"👤 Клиент: {client_name}\n"
        f"📅 Дата: {formatted_date}\n"
        f"🕐 Время: {appointment_time}\n"
        f"📋 Услуга: {service}\n\n"
        f"❗️ Это действие нельзя отменить!"
    )


def format_time_change_success(client_name, appointment_date, old_time, new_time, service):
    """Форматирует сообщение об успешном изменении времени"""
    date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
    formatted_date = format_date_russian(date_obj)

    return (
        f"✅ Время записи успешно изменено!\n\n"
        f"👤 Клиент: {client_name}\n"
        f"📅 Дата: {formatted_date}\n"
        f"🕐 Старое время: {old_time}\n"
        f"🕐 Новое время: {new_time}\n"
        f"📋 Услуга: {service}\n\n"
        f"📱 Не забудьте уведомить клиента об изменении!"
    )


def format_delete_success(client_name, appointment_date, appointment_time):
    """Форматирует сообщение об успешном удалении"""
    date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
    formatted_date = format_date_russian(date_obj)

    return (
        f"✅ Запись успешно удалена!\n\n"
        f"👤 Клиент: {client_name}\n"
        f"📅 Дата: {formatted_date}\n"
        f"🕐 Время: {appointment_time}\n\n"
        f"📱 Не забудьте уведомить клиента об отмене!"
    )


def format_appointment_confirmation(client_name, appointment_date, appointment_time, service):
    """Форматирует сообщение подтверждения новой записи"""
    try:
        date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        formatted_date = format_date_russian(date_obj)

        return (
            f"📋 Подтвердите добавление записи:\n\n"
            f"👤 Клиент: {client_name}\n"
            f"📅 Дата: {formatted_date}\n"
            f"🕐 Время: {appointment_time}\n"
            f"📋 Услуга: {service}\n\n"
            f"Все данные верны?"
        )
    except ValueError:
        return "❌ Ошибка форматирования данных"


def format_appointment_success(client_name, appointment_date, appointment_time, service, appointment_id):
    """Форматирует сообщение об успешном добавлении записи"""
    try:
        date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        formatted_date = format_date_russian(date_obj)

        return (
            f"✅ Запись успешно добавлена!\n\n"
            f"🆔 ID записи: {appointment_id}\n"
            f"👤 Клиент: {client_name}\n"
            f"📅 Дата: {formatted_date}\n"
            f"🕐 Время: {appointment_time}\n"
            f"📋 Услуга: {service}\n\n"
            f"📱 Не забудьте уведомить клиента!"
        )
    except ValueError:
        return "✅ Запись добавлена, но возникла ошибка форматирования"


def validate_client_name(name):
    """Валидация имени клиента"""
    return name.strip() != "" and len(name.strip()) >= 2


def validate_service_name(service):
    """Валидация названия услуги"""
    return service.strip() != "" and len(service.strip()) >= 2


def format_time_conflict(new_time, formatted_date, conflict_client):
    """Форматирует сообщение о конфликте времени"""
    return (
        f"⚠️ Время {new_time} на {formatted_date} уже занято клиентом: {conflict_client}\n"
        f"Выберите другое время."
    )