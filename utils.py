from datetime import datetime
from config import MONTHS, WEEKDAYS, SERVICES


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


def validate_client_name(name):
    """Валидация имени клиента"""
    return name.strip() != "" and len(name.strip()) >= 2


def validate_service_name(service):
    """Валидация названия услуги"""
    return service.strip() != "" and len(service.strip()) >= 2


def validate_phone_number(phone):
    """Валидация номера телефона"""
    if not phone:
        return True  # Телефон не обязателен

    # Убираем все символы кроме цифр и плюса
    clean_phone = ''.join(c for c in phone if c.isdigit() or c == '+')

    # Проверяем длину и формат
    if len(clean_phone) >= 10:
        return True
    return False


# ===== ФОРМАТИРОВАНИЕ ДЛЯ АДМИНИСТРАТОРА =====

def format_admin_schedule_text(appointments, target_date):
    """Форматирует расписание для администратора"""
    date_text = format_date_russian(target_date)

    if appointments:
        schedule_text = f"📅 Расписание на {date_text}:\n\n"

        if len(appointments[0]) == 4:  # С ID
            for appointment_id, client_name, appointment_time, service in appointments:
                schedule_text += f"🕐 {appointment_time} - {client_name}\n"
                schedule_text += f"📋 Услуга: {service}\n"
                schedule_text += f"🆔 ID: {appointment_id}\n\n"
        else:  # Без ID
            for client_name, appointment_time, service in appointments:
                schedule_text += f"🕐 {appointment_time} - {client_name}\n"
                schedule_text += f"📋 Услуга: {service}\n\n"
    else:
        schedule_text = f"📅 На {date_text} записей нет"

    return schedule_text


def format_admin_stats(stats):
    """Форматирует статистику для администратора"""
    return f"""📊 Статистика записей:

📅 Сегодня: {stats['today']} записей
➡️ Завтра: {stats['tomorrow']} записей  
📝 На неделю: {stats['week']} записей
📋 Всего записей: {stats['total']}
👥 Клиентов в базе: {stats['clients']}

Выберите период для подробного просмотра:"""


# ===== ФОРМАТИРОВАНИЕ ДЛЯ КЛИЕНТОВ =====

def format_client_appointments(appointments):
    """Форматирует список записей клиента"""
    if not appointments:
        return "📅 У вас пока нет активных записей.\n\nХотите записаться на услугу?"

    result = "📅 Ваши записи:\n\n"

    for appointment_id, client_name, appointment_date, appointment_time, service, status in appointments:
        date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        formatted_date = format_date_russian(date_obj)

        status_emoji = "✅" if status == "active" else "❌"

        result += f"{status_emoji} {formatted_date}\n"
        result += f"🕐 Время: {appointment_time}\n"
        result += f"📋 Услуга: {service}\n"
        result += f"🆔 ID: {appointment_id}\n\n"

    return result


def format_available_times_text(available_times, date_str):
    """Форматирует список доступного времени"""
    if not available_times:
        return f"😔 К сожалению, на {date_str} нет свободного времени.\n\nПопробуйте выбрать другую дату."

    date_obj = datetime.strptime(date_str, '%d.%m.%Y')
    formatted_date = format_date_russian(date_obj.date())

    times_text = ", ".join(available_times)

    return f"🕐 Доступное время на {formatted_date}:\n\n{times_text}\n\nВыберите подходящее время:"


def format_services_text():
    """Форматирует список услуг"""
    services_text = "📋 Доступные услуги:\n\n"

    service_emojis = {
        'Стрижка': '💇‍♀️',
        'Окрашивание': '🎨',
        'Маникюр': '💅',
        'Массаж': '💆‍♀️',
        'Косметология': '🧖‍♀️'
    }

    for service, duration in SERVICES.items():
        emoji = service_emojis.get(service, '📋')
        hours = duration // 60
        minutes = duration % 60

        if hours > 0 and minutes > 0:
            duration_text = f"{hours} ч {minutes} мин"
        elif hours > 0:
            duration_text = f"{hours} ч"
        else:
            duration_text = f"{minutes} мин"

        services_text += f"{emoji} {service} - {duration_text}\n"

    services_text += "\nВведите название услуги или выберите из списка:"
    return services_text


def format_booking_confirmation(client_name, appointment_date, appointment_time, service):
    """Форматирует подтверждение записи клиента"""
    try:
        date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        formatted_date = format_date_russian(date_obj)

        return f"""📋 Подтвердите запись:

👤 Имя: {client_name}
📅 Дата: {formatted_date}
🕐 Время: {appointment_time}
📋 Услуга: {service}

Все данные верны?"""
    except ValueError:
        return "❌ Ошибка форматирования данных"


def format_booking_success(appointment_id, client_name, appointment_date, appointment_time, service):
    """Форматирует сообщение об успешной записи"""
    try:
        date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        formatted_date = format_date_russian(date_obj)

        return f"""✅ Запись успешно создана!

🆔 Номер записи: {appointment_id}
👤 Клиент: {client_name}  
📅 Дата: {formatted_date}
🕐 Время: {appointment_time}
📋 Услуга: {service}

📱 Мы пришлем вам напоминание за день до визита.
💬 Если нужно что-то изменить, используйте кнопку "Мои записи"."""
    except ValueError:
        return "✅ Запись создана, но возникла ошибка форматирования"


def format_appointment_details(appointment_id, client_name, appointment_date, appointment_time, service):
    """Форматирует детальную информацию о записи"""
    date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
    formatted_date = format_date_russian(date_obj)

    return f"""📝 Детали записи:

🆔 ID: {appointment_id}
👤 Клиент: {client_name}
📅 Дата: {formatted_date}
🕐 Время: {appointment_time}
📋 Услуга: {service}

Выберите действие:"""


def format_cancel_confirmation_client(appointment_id, client_name, appointment_date, appointment_time, service):
    """Форматирует подтверждение отмены для клиента"""
    date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
    formatted_date = format_date_russian(date_obj)

    now = datetime.now().date()
    appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
    days_until = (appointment_date_obj - now).days

    warning = ""
    if days_until < 1:
        warning = "\n⚠️ Внимание! Отмена записи в день визита может повлечь штраф."

    return f"""❌ Отмена записи:

👤 Клиент: {client_name}
📅 Дата: {formatted_date}
🕐 Время: {appointment_time}
📋 Услуга: {service}{warning}

Вы уверены, что хотите отменить запись?"""


def format_reschedule_success(appointment_id, client_name, old_date, old_time, new_date, new_time, service):
    """Форматирует сообщение об успешном переносе"""
    old_date_obj = datetime.strptime(old_date, '%Y-%m-%d').date()
    new_date_obj = datetime.strptime(new_date, '%Y-%m-%d').date()

    old_formatted = format_date_russian(old_date_obj)
    new_formatted = format_date_russian(new_date_obj)

    return f"""✅ Запись успешно перенесена!

🆔 ID записи: {appointment_id}
👤 Клиент: {client_name}
📋 Услуга: {service}

📅 Было: {old_formatted}, {old_time}
📅 Стало: {new_formatted}, {new_time}

📱 Мы пришлем новое напоминание."""


# ===== ОБЩИЕ ФУНКЦИИ ФОРМАТИРОВАНИЯ =====

def format_appointment_info(appointment_id, client_name, appointment_date, appointment_time, service):
    """Универсальная функция форматирования информации о записи"""
    date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
    formatted_date = format_date_russian(date_obj)

    return f"""📝 Найдена запись:

🆔 ID: {appointment_id}
👤 Клиент: {client_name}
📅 Дата: {formatted_date}
🕐 Время: {appointment_time}
📋 Услуга: {service}

Выберите действие:"""


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

    return f"""⚠️ Подтвердите удаление записи:

👤 Клиент: {client_name}
📅 Дата: {formatted_date}
🕐 Время: {appointment_time}
📋 Услуга: {service}

❗️ Это действие нельзя отменить!"""


def format_time_change_success(client_name, appointment_date, old_time, new_time, service):
    """Форматирует сообщение об успешном изменении времени"""
    date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
    formatted_date = format_date_russian(date_obj)

    return f"""✅ Время записи успешно изменено!

👤 Клиент: {client_name}
📅 Дата: {formatted_date}
🕐 Старое время: {old_time}
🕐 Новое время: {new_time}
📋 Услуга: {service}

📱 Не забудьте уведомить клиента об изменении!"""


def format_delete_success(client_name, appointment_date, appointment_time):
    """Форматирует сообщение об успешном удалении"""
    date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
    formatted_date = format_date_russian(date_obj)

    return f"""✅ Запись успешно удалена!

👤 Клиент: {client_name}
📅 Дата: {formatted_date}
🕐 Время: {appointment_time}

📱 Не забудьте уведомить клиента об отмене!"""


def format_time_conflict(new_time, formatted_date, conflict_client):
    """Форматирует сообщение о конфликте времени"""
    return f"""⚠️ Время {new_time} на {formatted_date} уже занято клиентом: {conflict_client}

Выберите другое время."""


def get_contact_info():
    """Возвращает контактную информацию"""
    return """📞 Контактная информация:

🏢 Салон красоты "Стиль"
📍 Адрес: ул. Примерная, 123
📞 Телефон: +7 (999) 123-45-67
🕒 Часы работы: 09:00 - 21:00
📧 Email: info@style-salon.ru

🚗 Парковка есть
🚇 Рядом метро "Центральная"

Ждем вас! 💫"""


def get_about_info():
    """Возвращает информацию о салоне"""
    return """ℹ️ О нашем салоне:

🌟 Салон красоты "Стиль" - это:
✨ Опытные мастера с многолетним стажем
🎨 Современное оборудование
💎 Качественная косметика
🏆 Индивидуальный подход

👥 Наша команда:
💇‍♀️ Анна - топ-стилист
🎨 Мария - колорист
💅 Елена - мастер маникюра
💆‍♀️ Ольга - массажист

🎁 Постоянным клиентам - скидки!
📱 Удобная запись через бот
⏰ Напоминания о визитах

Добро пожаловать в мир красоты! 💫"""