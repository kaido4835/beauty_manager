from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_keyboard():
    """Создает основную клавиатуру меню"""
    btn_schedule = KeyboardButton(text="📅 Посмотреть расписание")
    btn_add = KeyboardButton(text="➕ Добавить запись")
    btn_search = KeyboardButton(text="🔍 Найти запись")
    btn_stats = KeyboardButton(text="📊 Статистика")

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [btn_schedule, btn_add],
            [btn_search, btn_stats]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_schedule_navigation_keyboard(day_offset=0):
    """Создает клавиатуру навигации для расписания"""
    builder = InlineKeyboardBuilder()

    if day_offset == 0:
        # Для первой страницы (сегодня)
        builder.button(text="📋 Выбрать дату", callback_data="select_date")
        builder.button(text="✏️ Редактировать", callback_data="edit_schedule")
        builder.button(text="➡️", callback_data="next_day_1")
        builder.adjust(3)  # 3 кнопки в ряду
    else:
        # Для других дней
        # Кнопка "Назад" (только если не сегодня)
        if day_offset > 0:
            builder.button(text="⬅️", callback_data=f"next_day_{day_offset - 1}")

        # Кнопка редактирования
        builder.button(text="✏️ Редактировать", callback_data="edit_schedule")

        # Кнопка "Вперед"
        builder.button(text="➡️", callback_data=f"next_day_{day_offset + 1}")

        # Размещаем кнопки
        if day_offset > 0:
            builder.adjust(3)  # 3 кнопки в ряду
        else:
            builder.adjust(2)  # 2 кнопки в ряду

    return builder.as_markup()


def get_appointment_actions_keyboard(appointment_id):
    """Создает клавиатуру действий с записью"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🕐 Изменить время", callback_data=f"time_{appointment_id}")
    builder.button(text="🗑 Удалить запись", callback_data=f"delete_{appointment_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_delete_confirmation_keyboard(appointment_id):
    """Создает клавиатуру подтверждения удаления"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"confirm_delete_{appointment_id}")
    builder.button(text="❌ Отмена", callback_data="cancel_delete")
    builder.adjust(2)
    return builder.as_markup()


def get_selected_date_keyboard():
    """Создает клавиатуру для выбранной даты"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Выбрать другую дату", callback_data="select_date")
    builder.button(text="✏️ Редактировать", callback_data="edit_schedule")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)  # Каждая кнопка на отдельной строке
    return builder.as_markup()


def get_add_appointment_confirmation_keyboard():
    """Создает клавиатуру подтверждения добавления записи"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_add_appointment")
    builder.button(text="❌ Отменить", callback_data="cancel_add_appointment")
    builder.adjust(2)
    return builder.as_markup()


def get_main_menu_inline_keyboard():
    """Создает инлайн клавиатуру для главного меню"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Сегодня", callback_data="schedule_today")
    builder.button(text="➡️ Завтра", callback_data="schedule_tomorrow")
    builder.button(text="📋 Выбрать дату", callback_data="select_date")
    builder.button(text="🔍 Поиск", callback_data="quick_search")
    builder.adjust(2, 2)  # 2 кнопки в первом ряду, 2 во втором
    return builder.as_markup()


def get_cancel_add_keyboard():
    """Создает клавиатуру для отмены добавления"""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отменить добавление", callback_data="cancel_add_appointment")
    return builder.as_markup()


def get_edit_schedule_keyboard():
    """Создает клавиатуру для редактирования расписания"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data="edit_schedule")
    return builder.as_markup()