from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ===== КЛАВИАТУРЫ ДЛЯ АДМИНИСТРАТОРА =====

def get_admin_menu_keyboard():
    """Создает основную клавиатуру меню для администратора"""
    btn_schedule = KeyboardButton(text="📅 Все записи")
    btn_add = KeyboardButton(text="➕ Добавить запись")
    btn_search = KeyboardButton(text="🔍 Найти запись")
    btn_stats = KeyboardButton(text="📊 Статистика")
    btn_clients = KeyboardButton(text="👥 Клиенты")
    btn_settings = KeyboardButton(text="⚙️ Настройки")

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [btn_schedule, btn_add],
            [btn_search, btn_stats],
            [btn_clients, btn_settings]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_admin_schedule_keyboard(day_offset=0):
    """Создает клавиатуру навигации для расписания (админ)"""
    builder = InlineKeyboardBuilder()

    if day_offset == 0:
        # Для первой страницы (сегодня)
        builder.button(text="📋 Выбрать дату", callback_data="admin_select_date")
        builder.button(text="✏️ Редактировать", callback_data="admin_edit_schedule")
        builder.button(text="➡️", callback_data=f"admin_next_day_{day_offset + 1}")
        builder.adjust(3)
    else:
        # Для других дней
        if day_offset > 0:
            builder.button(text="⬅️", callback_data=f"admin_next_day_{day_offset - 1}")

        builder.button(text="✏️ Редактировать", callback_data="admin_edit_schedule")
        builder.button(text="➡️", callback_data=f"admin_next_day_{day_offset + 1}")

        if day_offset > 0:
            builder.adjust(3)
        else:
            builder.adjust(2)

    return builder.as_markup()


def get_admin_appointment_actions_keyboard(appointment_id):
    """Создает клавиатуру действий с записью (админ)"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🕐 Изменить время", callback_data=f"admin_time_{appointment_id}")
    builder.button(text="👤 Изменить клиента", callback_data=f"admin_client_{appointment_id}")
    builder.button(text="📋 Изменить услугу", callback_data=f"admin_service_{appointment_id}")
    builder.button(text="🗑 Удалить запись", callback_data=f"admin_delete_{appointment_id}")
    builder.adjust(2, 2)
    return builder.as_markup()


# ===== КЛАВИАТУРЫ ДЛЯ КЛИЕНТОВ =====

def get_client_menu_keyboard():
    """Создает основную клавиатуру меню для клиентов"""
    btn_my_appointments = KeyboardButton(text="📅 Мои записи")
    btn_book = KeyboardButton(text="➕ Записаться")
    btn_reschedule = KeyboardButton(text="🔄 Перенести запись")
    btn_cancel = KeyboardButton(text="❌ Отменить запись")
    btn_contact = KeyboardButton(text="📞 Контакты")
    btn_info = KeyboardButton(text="ℹ️ О нас")

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [btn_my_appointments, btn_book],
            [btn_reschedule, btn_cancel],
            [btn_contact, btn_info]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_client_appointments_keyboard(user_id):
    """Создает клавиатуру для просмотра записей клиента"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data=f"client_refresh_appointments_{user_id}")
    builder.button(text="➕ Записаться еще", callback_data="client_book_new")
    builder.button(text="🏠 Главное меню", callback_data="client_main_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_available_times_keyboard(available_times, date):
    """Создает клавиатуру с доступным временем"""
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки времени по 3 в ряду
    for time in available_times:
        builder.button(text=time, callback_data=f"client_select_time_{time}_{date}")

    builder.button(text="📅 Другая дата", callback_data="client_select_other_date")
    builder.button(text="❌ Отмена", callback_data="client_cancel_booking")

    builder.adjust(3)  # По 3 кнопки времени в ряду
    return builder.as_markup()


def get_services_keyboard():
    """Создает клавиатуру с доступными услугами"""
    builder = InlineKeyboardBuilder()

    services = [
        ("💇‍♀️ Стрижка", "Стрижка"),
        ("🎨 Окрашивание", "Окрашивание"),
        ("💅 Маникюр", "Маникюр"),
        ("💆‍♀️ Массаж", "Массаж"),
        ("🧖‍♀️ Косметология", "Косметология")
    ]

    for display_name, service_name in services:
        builder.button(text=display_name, callback_data=f"client_select_service_{service_name}")

    builder.button(text="❌ Отмена", callback_data="client_cancel_booking")
    builder.adjust(1)
    return builder.as_markup()


def get_appointment_confirmation_keyboard():
    """Создает клавиатуру подтверждения записи"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить запись", callback_data="client_confirm_booking")
    builder.button(text="🔄 Изменить время", callback_data="client_change_time")
    builder.button(text="📋 Другая услуга", callback_data="client_change_service")
    builder.button(text="❌ Отмена", callback_data="client_cancel_booking")
    builder.adjust(2, 2)
    return builder.as_markup()


def get_client_appointment_actions_keyboard(appointment_id):
    """Создает клавиатуру действий с записью клиента"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Перенести", callback_data=f"client_reschedule_{appointment_id}")
    builder.button(text="❌ Отменить", callback_data=f"client_cancel_{appointment_id}")
    builder.button(text="ℹ️ Подробнее", callback_data=f"client_details_{appointment_id}")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_cancel_confirmation_keyboard(appointment_id):
    """Создает клавиатуру подтверждения отмены"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, отменить", callback_data=f"client_confirm_cancel_{appointment_id}")
    builder.button(text="❌ Нет, оставить", callback_data="client_keep_appointment")
    builder.adjust(2)
    return builder.as_markup()


# ===== ОБЩИЕ КЛАВИАТУРЫ =====

def get_delete_confirmation_keyboard(appointment_id, user_type="admin"):
    """Создает клавиатуру подтверждения удаления"""
    builder = InlineKeyboardBuilder()
    prefix = "admin" if user_type == "admin" else "client"
    builder.button(text="✅ Да, удалить", callback_data=f"{prefix}_confirm_delete_{appointment_id}")
    builder.button(text="❌ Отмена", callback_data=f"{prefix}_cancel_delete")
    builder.adjust(2)
    return builder.as_markup()


def get_selected_date_keyboard(user_type="admin"):
    """Создает клавиатуру для выбранной даты"""
    builder = InlineKeyboardBuilder()
    prefix = "admin" if user_type == "admin" else "client"

    builder.button(text="📋 Выбрать другую дату", callback_data=f"{prefix}_select_date")

    if user_type == "admin":
        builder.button(text="✏️ Редактировать", callback_data="admin_edit_schedule")
    else:
        builder.button(text="➕ Записаться", callback_data="client_book_new")

    builder.button(text="🏠 Главное меню", callback_data=f"{prefix}_main_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_cancel_operation_keyboard(user_type="admin", operation="add"):
    """Создает клавиатуру для отмены операции"""
    builder = InlineKeyboardBuilder()
    prefix = "admin" if user_type == "admin" else "client"

    if operation == "add":
        callback = f"{prefix}_cancel_add_appointment"
        text = "❌ Отменить добавление"
    elif operation == "booking":
        callback = "client_cancel_booking"
        text = "❌ Отменить запись"
    else:
        callback = f"{prefix}_cancel_operation"
        text = "❌ Отменить"

    builder.button(text=text, callback_data=callback)
    return builder.as_markup()


def get_date_navigation_keyboard(current_date, user_type="client"):
    """Создает клавиатуру навигации по датам"""
    builder = InlineKeyboardBuilder()
    prefix = "client" if user_type == "client" else "admin"

    # Кнопки навигации по дням
    builder.button(text="⬅️ Вчера", callback_data=f"{prefix}_date_prev_{current_date}")
    builder.button(text="📅 Сегодня", callback_data=f"{prefix}_date_today")
    builder.button(text="➡️ Завтра", callback_data=f"{prefix}_date_next_{current_date}")

    # Кнопка выбора произвольной даты
    builder.button(text="📋 Выбрать дату", callback_data=f"{prefix}_select_custom_date")

    builder.adjust(3, 1)
    return builder.as_markup()