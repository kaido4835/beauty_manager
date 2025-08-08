import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery

from config import TOKEN, COMMON_MESSAGES, ADMIN_MESSAGES, CLIENT_MESSAGES, SERVICES, ADMIN_ID


async def main():
    """Главная функция запуска бота"""
    print("🤖 Бот запускается...")
    print(f"👨‍💼 ID администратора: {ADMIN_ID}")

    # Создаем хранилище для состояний и инициализируем бота
    storage = MemoryStorage()
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=storage)

    # Подключаем роутер с обработчиками
    dp.include_router(router)

    print("🚀 Бот успешно запущен и готов к работе!")
    print("📱 Администратор получит расширенный функционал")
    print("👥 Клиенты получат интерфейс для записи")
    print("📊 Ожидание сообщений...")

    # Запускаем бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    from config import ADMIN_ID

    asyncio.run(main())
from database import (
    get_schedule_by_date, get_schedule_by_specific_date, get_stats_summary,
    get_client_appointments, get_available_times, book_appointment,
    cancel_appointment_by_client, reschedule_appointment, search_appointment,
    delete_appointment, update_appointment_time, update_appointment_client,
    update_appointment_service, check_time_conflict, get_appointment_by_id,
    add_appointment, get_client_info
)
from keyboards import (
    get_admin_menu_keyboard, get_admin_schedule_keyboard, get_admin_appointment_actions_keyboard,
    get_client_menu_keyboard, get_client_appointments_keyboard, get_available_times_keyboard,
    get_services_keyboard, get_appointment_confirmation_keyboard, get_client_appointment_actions_keyboard,
    get_cancel_confirmation_keyboard, get_delete_confirmation_keyboard, get_selected_date_keyboard,
    get_cancel_operation_keyboard, get_date_navigation_keyboard
)
from utils import (
    validate_time_format, validate_date_format, validate_client_name, validate_service_name,
    format_admin_schedule_text, format_admin_stats, format_client_appointments,
    format_available_times_text, format_services_text, format_booking_confirmation,
    format_booking_success, format_appointment_details, format_cancel_confirmation_client,
    format_reschedule_success, format_appointment_info, format_multiple_appointments,
    format_delete_confirmation, format_time_change_success, format_delete_success,
    format_time_conflict, get_contact_info, get_about_info, format_date_russian
)
from states import (
    AdminEditStates, AdminAddStates, ClientBookingStates,
    ClientRescheduleStates, ClientCancelStates
)

# Создаем роутер для обработчиков
router = Router()


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id == ADMIN_ID


# ===== КОМАНДА START =====

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start с разделением на админа и клиентов"""
    user_id = message.from_user.id

    if is_admin(user_id):
        # Приветствие для администратора
        stats = get_stats_summary()
        welcome_text = ADMIN_MESSAGES['main_menu_welcome'].format(
            today_count=stats['today'],
            tomorrow_count=stats['tomorrow'],
            week_count=stats['week']
        )
        keyboard = get_admin_menu_keyboard()
    else:
        # Приветствие для клиента
        welcome_text = CLIENT_MESSAGES['welcome']
        keyboard = get_client_menu_keyboard()

        # Сохраняем информацию о клиенте, если есть
        if message.from_user.first_name:
            # Можно сразу попытаться зарегистрировать базовую информацию
            pass

    await message.answer(welcome_text, reply_markup=keyboard)


# ===== ОБРАБОТЧИКИ СООБЩЕНИЙ ДЛЯ АДМИНИСТРАТОРА =====

@router.message(lambda message: is_admin(message.from_user.id))
async def handle_admin_messages(message: Message, state: FSMContext):
    """Обработчик сообщений администратора"""
    current_state = await state.get_state()

    # === СОСТОЯНИЯ РЕДАКТИРОВАНИЯ ===
    if current_state == AdminEditStates.waiting_for_search:
        await handle_admin_search(message, state)

    elif current_state == AdminEditStates.waiting_for_new_time:
        await handle_admin_time_change(message, state)

    elif current_state == AdminEditStates.waiting_for_new_client:
        await handle_admin_client_change(message, state)

    elif current_state == AdminEditStates.waiting_for_new_service:
        await handle_admin_service_change(message, state)

    elif current_state == AdminEditStates.waiting_for_date:
        await handle_admin_date_input(message, state)

    # === СОСТОЯНИЯ ДОБАВЛЕНИЯ ===
    elif current_state == AdminAddStates.waiting_for_client_name:
        await handle_admin_add_client_name(message, state)

    elif current_state == AdminAddStates.waiting_for_appointment_date:
        await handle_admin_add_date(message, state)

    elif current_state == AdminAddStates.waiting_for_appointment_time:
        await handle_admin_add_time(message, state)

    elif current_state == AdminAddStates.waiting_for_service:
        await handle_admin_add_service(message, state)

    # === ОБЫЧНЫЕ КОМАНДЫ ===
    elif message.text == "📅 Все записи":
        await show_admin_schedule(message, 0)

    elif message.text == "➕ Добавить запись":
        await start_admin_add_appointment(message, state)

    elif message.text == "🔍 Найти запись":
        await message.answer(ADMIN_MESSAGES['search_prompt'])
        await state.set_state(AdminEditStates.waiting_for_search)

    elif message.text == "📊 Статистика":
        await show_admin_stats(message)

    elif message.text == "👥 Клиенты":
        await show_admin_clients(message)

    elif message.text == "⚙️ Настройки":
        await show_admin_settings(message)

    else:
        if not current_state:
            await message.answer(COMMON_MESSAGES['unknown_command'])


# ===== ОБРАБОТЧИКИ СООБЩЕНИЙ ДЛЯ КЛИЕНТОВ =====

@router.message(lambda message: not is_admin(message.from_user.id))
async def handle_client_messages(message: Message, state: FSMContext):
    """Обработчик сообщений клиентов"""
    current_state = await state.get_state()
    user_id = message.from_user.id

    # === СОСТОЯНИЯ ЗАПИСИ ===
    if current_state == ClientBookingStates.waiting_for_name:
        await handle_client_name_input(message, state)

    elif current_state == ClientBookingStates.waiting_for_date:
        await handle_client_date_input(message, state)

    elif current_state == ClientBookingStates.waiting_for_time:
        await handle_client_time_input(message, state)

    elif current_state == ClientBookingStates.waiting_for_service:
        await handle_client_service_input(message, state)

    # === СОСТОЯНИЯ ПЕРЕНОСА ===
    elif current_state == ClientRescheduleStates.waiting_for_appointment_selection:
        await handle_client_reschedule_selection(message, state)

    elif current_state == ClientRescheduleStates.waiting_for_new_date:
        await handle_client_reschedule_date(message, state)

    elif current_state == ClientRescheduleStates.waiting_for_new_time:
        await handle_client_reschedule_time(message, state)

    # === СОСТОЯНИЯ ОТМЕНЫ ===
    elif current_state == ClientCancelStates.waiting_for_appointment_selection:
        await handle_client_cancel_selection(message, state)

    # === ОБЫЧНЫЕ КОМАНДЫ ===
    elif message.text == "📅 Мои записи":
        await show_client_appointments(message, user_id)

    elif message.text == "➕ Записаться":
        await start_client_booking(message, state)

    elif message.text == "🔄 Перенести запись":
        await start_client_reschedule(message, state, user_id)

    elif message.text == "❌ Отменить запись":
        await start_client_cancel(message, state, user_id)

    elif message.text == "📞 Контакты":
        await message.answer(get_contact_info())

    elif message.text == "ℹ️ О нас":
        await message.answer(get_about_info())

    else:
        if not current_state:
            await message.answer(COMMON_MESSAGES['unknown_command'])


# ===== ОБРАБОТЧИК CALLBACK ЗАПРОСОВ =====

@router.callback_query()
async def handle_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик всех callback запросов"""
    user_id = callback.from_user.id
    data = callback.data

    # Определяем тип пользователя и направляем к соответствующему обработчику
    if is_admin(user_id):
        await handle_admin_callback(callback, state, data)
    else:
        await handle_client_callback(callback, state, data, user_id)

    await callback.answer()


async def handle_admin_callback(callback: CallbackQuery, state: FSMContext, data: str):
    """Обработчик callback запросов администратора"""

    # Навигация по расписанию
    if data.startswith("admin_next_day_"):
        day_offset = int(data.replace("admin_next_day_", ""))
        appointments, target_date = get_schedule_by_date(day_offset)
        schedule_text = format_admin_schedule_text(appointments, target_date)
        keyboard = get_admin_schedule_keyboard(day_offset)
        await callback.message.edit_text(schedule_text, reply_markup=keyboard)

    # Выбор даты
    elif data == "admin_select_date":
        await callback.message.edit_text(ADMIN_MESSAGES['date_prompt'])
        await state.set_state(AdminEditStates.waiting_for_date)

    # Редактирование расписания
    elif data == "admin_edit_schedule":
        await callback.message.edit_text(ADMIN_MESSAGES['search_prompt'])
        await state.set_state(AdminEditStates.waiting_for_search)

    # Действия с записью
    elif data.startswith("admin_time_"):
        appointment_id = data.replace("admin_time_", "")
        await state.update_data(appointment_id=appointment_id)
        await callback.message.edit_text("🕐 Введите новое время записи (ЧЧ:ММ):")
        await state.set_state(AdminEditStates.waiting_for_new_time)

    elif data.startswith("admin_client_"):
        appointment_id = data.replace("admin_client_", "")
        await state.update_data(appointment_id=appointment_id)
        await callback.message.edit_text("👤 Введите новое имя клиента:")
        await state.set_state(AdminEditStates.waiting_for_new_client)

    elif data.startswith("admin_service_"):
        appointment_id = data.replace("admin_service_", "")
        await state.update_data(appointment_id=appointment_id)
        await callback.message.edit_text("📋 Введите новую услугу:")
        await state.set_state(AdminEditStates.waiting_for_new_service)

    elif data.startswith("admin_delete_"):
        appointment_id = data.replace("admin_delete_", "")
        appointment_info = get_appointment_by_id(appointment_id)

        if appointment_info:
            client_name, appointment_date, appointment_time, service, _ = appointment_info
            confirmation_text = format_delete_confirmation(
                client_name, appointment_date, appointment_time, service
            )
            keyboard = get_delete_confirmation_keyboard(appointment_id, "admin")
            await callback.message.edit_text(confirmation_text, reply_markup=keyboard)

    # Подтверждение удаления
    elif data.startswith("admin_confirm_delete_"):
        appointment_id = data.replace("admin_confirm_delete_", "")
        appointment_info = get_appointment_by_id(appointment_id)

        if appointment_info:
            client_name, appointment_date, appointment_time, _, _ = appointment_info
            delete_appointment(appointment_id)
            success_text = format_delete_success(client_name, appointment_date, appointment_time)
            await callback.message.edit_text(success_text)
        await state.clear()

    # Отмена удаления
    elif data == "admin_cancel_delete":
        await callback.message.edit_text(COMMON_MESSAGES['delete_cancelled'])
        await state.clear()

    # Главное меню администратора
    elif data == "admin_main_menu":
        await state.clear()
        stats = get_stats_summary()
        welcome_text = ADMIN_MESSAGES['main_menu_welcome'].format(
            today_count=stats['today'],
            tomorrow_count=stats['tomorrow'],
            week_count=stats['week']
        )
        keyboard = get_admin_menu_keyboard()
        await callback.message.edit_text(welcome_text, reply_markup=keyboard)


async def handle_client_callback(callback: CallbackQuery, state: FSMContext, data: str, user_id: int):
    """Обработчик callback запросов клиентов"""

    # Обновление списка записей
    if data.startswith("client_refresh_appointments_"):
        await show_client_appointments(callback.message, user_id, edit=True)

    # Новая запись
    elif data == "client_book_new":
        await start_client_booking(callback.message, state, edit=True)

    # Выбор времени
    elif data.startswith("client_select_time_"):
        parts = data.replace("client_select_time_", "").split("_")
        time = parts[0]
        date = parts[1]

        await state.update_data(appointment_time=time)

        # Переходим к выбору услуги
        services_text = format_services_text()
        keyboard = get_services_keyboard()
        await callback.message.edit_text(services_text, reply_markup=keyboard)

    # Выбор услуги
    elif data.startswith("client_select_service_"):
        service = data.replace("client_select_service_", "")
        await state.update_data(service=service)

        # Показываем подтверждение
        booking_data = await state.get_data()
        confirmation_text = format_booking_confirmation(
            booking_data['client_name'],
            booking_data['appointment_date'],
            booking_data['appointment_time'],
            service
        )
        keyboard = get_appointment_confirmation_keyboard()
        await callback.message.edit_text(confirmation_text, reply_markup=keyboard)

    # Подтверждение записи
    elif data == "client_confirm_booking":
        booking_data = await state.get_data()

        appointment_id = book_appointment(
            user_id,
            booking_data['client_name'],
            booking_data['appointment_date'],
            booking_data['appointment_time'],
            booking_data['service']
        )

        success_text = format_booking_success(
            appointment_id,
            booking_data['client_name'],
            booking_data['appointment_date'],
            booking_data['appointment_time'],
            booking_data['service']
        )

        await callback.message.edit_text(success_text)
        await state.clear()

    # Отмена записи
    elif data == "client_cancel_booking":
        await callback.message.edit_text("❌ Запись отменена")
        await state.clear()

    # Действия с существующими записями
    elif data.startswith("client_reschedule_"):
        appointment_id = data.replace("client_reschedule_", "")
        await start_reschedule_process(callback.message, state, appointment_id, user_id, edit=True)

    elif data.startswith("client_cancel_"):
        appointment_id = data.replace("client_cancel_", "")
        await start_cancel_process(callback.message, state, appointment_id, user_id, edit=True)

    elif data.startswith("client_details_"):
        appointment_id = data.replace("client_details_", "")
        await show_appointment_details(callback.message, appointment_id, edit=True)

    # Подтверждение отмены записи
    elif data.startswith("client_confirm_cancel_"):
        appointment_id = data.replace("client_confirm_cancel_", "")

        if cancel_appointment_by_client(appointment_id, user_id):
            await callback.message.edit_text("✅ Запись успешно отменена!")
        else:
            await callback.message.edit_text("❌ Не удалось отменить запись")

        await state.clear()

    # Оставить запись
    elif data == "client_keep_appointment":
        await callback.message.edit_text("✅ Запись сохранена")
        await state.clear()

    # Главное меню клиента
    elif data == "client_main_menu":
        await state.clear()
        keyboard = get_client_menu_keyboard()
        await callback.message.edit_text(CLIENT_MESSAGES['welcome'], reply_markup=keyboard)


# ===== ФУНКЦИИ АДМИНИСТРАТОРА =====

async def show_admin_schedule(message: Message, day_offset: int):
    """Показывает расписание администратору"""
    appointments, target_date = get_schedule_by_date(day_offset)
    schedule_text = format_admin_schedule_text(appointments, target_date)
    keyboard = get_admin_schedule_keyboard(day_offset)
    await message.answer(schedule_text, reply_markup=keyboard)


async def show_admin_stats(message: Message):
    """Показывает статистику администратору"""
    stats = get_stats_summary()
    stats_text = format_admin_stats(stats)
    await message.answer(stats_text)


async def show_admin_clients(message: Message):
    """Показывает список клиентов администратору"""
    # TODO: Реализовать показ клиентов
    await message.answer("👥 Управление клиентами\n\nВ разработке...")


async def show_admin_settings(message: Message):
    """Показывает настройки администратору"""
    # TODO: Реализовать настройки
    await message.answer("⚙️ Настройки\n\nВ разработке...")


async def start_admin_add_appointment(message: Message, state: FSMContext):
    """Начинает процесс добавления записи администратором"""
    keyboard = get_cancel_operation_keyboard("admin", "add")
    await message.answer("👤 Введите имя клиента:", reply_markup=keyboard)
    await state.set_state(AdminAddStates.waiting_for_client_name)


# Функции обработки состояний администратора
async def handle_admin_search(message: Message, state: FSMContext):
    """Обрабатывает поиск записи администратором"""
    search_term = message.text.strip()
    appointments = search_appointment(search_term)

    if not appointments:
        await message.answer(COMMON_MESSAGES['not_found'])
        return

    if len(appointments) == 1:
        appointment_id, client_name, appointment_date, appointment_time, service = appointments[0]
        info_text = format_appointment_info(
            appointment_id, client_name, appointment_date, appointment_time, service
        )
        keyboard = get_admin_appointment_actions_keyboard(appointment_id)
        await message.answer(info_text, reply_markup=keyboard)
    else:
        result_text = format_multiple_appointments(appointments)
        await message.answer(result_text)

    await state.clear()


async def handle_admin_time_change(message: Message, state: FSMContext):
    """Обрабатывает изменение времени администратором"""
    new_time = message.text.strip()

    if not validate_time_format(new_time):
        await message.answer(COMMON_MESSAGES['time_format_error'])
        return

    data = await state.get_data()
    appointment_id = data.get('appointment_id')
    appointment_info = get_appointment_by_id(appointment_id)

    if appointment_info:
        client_name, appointment_date, old_time, service, _ = appointment_info

        # Проверяем конфликт времени
        conflict = check_time_conflict(new_time, appointment_date, appointment_id)

        if conflict:
            date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            formatted_date = format_date_russian(date_obj)
            conflict_text = format_time_conflict(new_time, formatted_date, conflict[0])
            await message.answer(conflict_text)
        else:
            update_appointment_time(appointment_id, new_time)
            success_text = format_time_change_success(
                client_name, appointment_date, old_time, new_time, service
            )
            await message.answer(success_text)
    else:
        await message.answer(COMMON_MESSAGES['appointment_not_found'])

    await state.clear()


async def handle_admin_client_change(message: Message, state: FSMContext):
    """Обрабатывает изменение клиента администратором"""
    new_client_name = message.text.strip()

    if not validate_client_name(new_client_name):
        await message.answer(COMMON_MESSAGES['invalid_client_name'])
        return

    data = await state.get_data()
    appointment_id = data.get('appointment_id')

    update_appointment_client(appointment_id, new_client_name)
    await message.answer(f"✅ Имя клиента изменено на: {new_client_name}")
    await state.clear()


async def handle_admin_service_change(message: Message, state: FSMContext):
    """Обрабатывает изменение услуги администратором"""
    new_service = message.text.strip()

    if not validate_service_name(new_service):
        await message.answer(COMMON_MESSAGES['invalid_service'])
        return

    data = await state.get_data()
    appointment_id = data.get('appointment_id')

    update_appointment_service(appointment_id, new_service)
    await message.answer(f"✅ Услуга изменена на: {new_service}")
    await state.clear()


async def handle_admin_date_input(message: Message, state: FSMContext):
    """Обрабатывает ввод даты администратором"""
    date_input = message.text.strip()

    if not validate_date_format(date_input):
        await message.answer(COMMON_MESSAGES['date_format_error'])
        return

    appointments, target_date = get_schedule_by_specific_date(date_input)

    if target_date is None:
        await message.answer(COMMON_MESSAGES['error_processing_date'])
        return

    schedule_text = format_admin_schedule_text(appointments, target_date)
    keyboard = get_selected_date_keyboard("admin")

    await message.answer(schedule_text, reply_markup=keyboard)
    await state.clear()


async def handle_admin_add_client_name(message: Message, state: FSMContext):
    """Обрабатывает ввод имени клиента при добавлении записи"""
    client_name = message.text.strip()

    if not validate_client_name(client_name):
        keyboard = get_cancel_operation_keyboard("admin", "add")
        await message.answer(COMMON_MESSAGES['invalid_client_name'], reply_markup=keyboard)
        return

    await state.update_data(client_name=client_name)
    keyboard = get_cancel_operation_keyboard("admin", "add")
    await message.answer("📅 Введите дату записи (ДД.ММ.ГГГГ):", reply_markup=keyboard)
    await state.set_state(AdminAddStates.waiting_for_appointment_date)


async def handle_admin_add_date(message: Message, state: FSMContext):
    """Обрабатывает ввод даты при добавлении записи"""
    date_input = message.text.strip()

    if not validate_date_format(date_input):
        keyboard = get_cancel_operation_keyboard("admin", "add")
        await message.answer(COMMON_MESSAGES['date_format_error'], reply_markup=keyboard)
        return

    try:
        appointment_date = datetime.strptime(date_input, '%d.%m.%Y').date().strftime('%Y-%m-%d')
        await state.update_data(appointment_date=appointment_date)

        keyboard = get_cancel_operation_keyboard("admin", "add")
        await message.answer("🕐 Введите время записи (ЧЧ:ММ):", reply_markup=keyboard)
        await state.set_state(AdminAddStates.waiting_for_appointment_time)
    except ValueError:
        keyboard = get_cancel_operation_keyboard("admin", "add")
        await message.answer(COMMON_MESSAGES['error_processing_date'], reply_markup=keyboard)


async def handle_admin_add_time(message: Message, state: FSMContext):
    """Обрабатывает ввод времени при добавлении записи"""
    time_input = message.text.strip()

    if not validate_time_format(time_input):
        keyboard = get_cancel_operation_keyboard("admin", "add")
        await message.answer(COMMON_MESSAGES['time_format_error'], reply_markup=keyboard)
        return

    data = await state.get_data()
    appointment_date = data.get('appointment_date')

    # Проверяем конфликт времени
    conflict = check_time_conflict(time_input, appointment_date)
    if conflict:
        date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        formatted_date = format_date_russian(date_obj)
        conflict_text = format_time_conflict(time_input, formatted_date, conflict[0])

        keyboard = get_cancel_operation_keyboard("admin", "add")
        await message.answer(conflict_text, reply_markup=keyboard)
        return

    await state.update_data(appointment_time=time_input)
    keyboard = get_cancel_operation_keyboard("admin", "add")
    await message.answer("📋 Введите название услуги:", reply_markup=keyboard)
    await state.set_state(AdminAddStates.waiting_for_service)


async def handle_admin_add_service(message: Message, state: FSMContext):
    """Обрабатывает ввод услуги при добавлении записи"""
    service = message.text.strip()

    if not validate_service_name(service):
        keyboard = get_cancel_operation_keyboard("admin", "add")
        await message.answer(COMMON_MESSAGES['invalid_service'], reply_markup=keyboard)
        return

    # Добавляем запись
    data = await state.get_data()
    appointment_id = add_appointment(
        data['client_name'],
        data['appointment_date'],
        data['appointment_time'],
        service
    )

    success_text = f"""✅ Запись успешно добавлена!

🆔 ID записи: {appointment_id}
👤 Клиент: {data['client_name']}
📅 Дата: {data['appointment_date']}
🕐 Время: {data['appointment_time']}
📋 Услуга: {service}"""

    await message.answer(success_text)
    await state.clear()


# ===== ФУНКЦИИ КЛИЕНТОВ =====

async def show_client_appointments(message: Message, user_id: int, edit: bool = False):
    """Показывает записи клиента"""
    appointments = get_client_appointments(user_id)
    appointments_text = format_client_appointments(appointments)
    keyboard = get_client_appointments_keyboard(user_id)

    if edit:
        await message.edit_text(appointments_text, reply_markup=keyboard)
    else:
        await message.answer(appointments_text, reply_markup=keyboard)


async def start_client_booking(message: Message, state: FSMContext, edit: bool = False):
    """Начинает процесс записи клиента"""
    booking_text = CLIENT_MESSAGES['book_appointment']
    keyboard = get_cancel_operation_keyboard("client", "booking")

    if edit:
        await message.edit_text(booking_text, reply_markup=keyboard)
    else:
        await message.answer(booking_text, reply_markup=keyboard)

    await state.set_state(ClientBookingStates.waiting_for_name)


async def start_client_reschedule(message: Message, state: FSMContext, user_id: int):
    """Начинает процесс переноса записи клиента"""
    appointments = get_client_appointments(user_id)

    if not appointments:
        await message.answer(CLIENT_MESSAGES['no_appointments'])
        return

    appointments_text = format_client_appointments(appointments)
    reschedule_text = f"{CLIENT_MESSAGES['reschedule_appointment']}\n\n{appointments_text}\n\nВведите ID записи для переноса:"

    await message.answer(reschedule_text)
    await state.set_state(ClientRescheduleStates.waiting_for_appointment_selection)


async def start_client_cancel(message: Message, state: FSMContext, user_id: int):
    """Начинает процесс отмены записи клиента"""
    appointments = get_client_appointments(user_id)

    if not appointments:
        await message.answer(CLIENT_MESSAGES['no_appointments'])
        return

    appointments_text = format_client_appointments(appointments)
    cancel_text = f"{CLIENT_MESSAGES['cancel_appointment']}\n\n{appointments_text}\n\nВведите ID записи для отмены:"

    await message.answer(cancel_text)
    await state.set_state(ClientCancelStates.waiting_for_appointment_selection)


# Функции обработки состояний клиентов
async def handle_client_name_input(message: Message, state: FSMContext):
    """Обрабатывает ввод имени клиента"""
    client_name = message.text.strip()

    if not validate_client_name(client_name):
        keyboard = get_cancel_operation_keyboard("client", "booking")
        await message.answer(COMMON_MESSAGES['invalid_client_name'], reply_markup=keyboard)
        return

    await state.update_data(client_name=client_name)
    keyboard = get_cancel_operation_keyboard("client", "booking")
    await message.answer("📅 Введите желаемую дату (ДД.ММ.ГГГГ):", reply_markup=keyboard)
    await state.set_state(ClientBookingStates.waiting_for_date)


async def handle_client_date_input(message: Message, state: FSMContext):
    """Обрабатывает ввод даты клиента"""
    date_input = message.text.strip()

    if not validate_date_format(date_input):
        keyboard = get_cancel_operation_keyboard("client", "booking")
        await message.answer(COMMON_MESSAGES['date_format_error'], reply_markup=keyboard)
        return

    try:
        # Проверяем, что дата не в прошлом
        target_date = datetime.strptime(date_input, '%d.%m.%Y').date()
        today = datetime.now().date()

        if target_date < today:
            keyboard = get_cancel_operation_keyboard("client", "booking")
            await message.answer("❌ Нельзя записаться на прошедшую дату. Выберите сегодня или будущую дату:",
                                 reply_markup=keyboard)
            return

        appointment_date = target_date.strftime('%Y-%m-%d')
        await state.update_data(appointment_date=appointment_date)

        # Получаем доступное время
        available_times = get_available_times(date_input)

        if not available_times:
            keyboard = get_cancel_operation_keyboard("client", "booking")
            no_time_text = CLIENT_MESSAGES['no_available_times']
            await message.answer(no_time_text, reply_markup=keyboard)
            return

        # Показываем доступное время
        times_text = format_available_times_text(available_times, date_input)
        keyboard = get_available_times_keyboard(available_times, date_input)
        await message.answer(times_text, reply_markup=keyboard)

    except ValueError:
        keyboard = get_cancel_operation_keyboard("client", "booking")
        await message.answer(COMMON_MESSAGES['error_processing_date'], reply_markup=keyboard)


async def handle_client_time_input(message: Message, state: FSMContext):
    """Обрабатывает ввод времени клиента (если введено вручную)"""
    time_input = message.text.strip()

    if not validate_time_format(time_input):
        keyboard = get_cancel_operation_keyboard("client", "booking")
        await message.answer(COMMON_MESSAGES['time_format_error'], reply_markup=keyboard)
        return

    data = await state.get_data()
    appointment_date = data.get('appointment_date')

    # Проверяем доступность времени
    date_str = datetime.strptime(appointment_date, '%Y-%m-%d').strftime('%d.%m.%Y')
    available_times = get_available_times(date_str)

    if time_input not in available_times:
        keyboard = get_cancel_operation_keyboard("client", "booking")
        await message.answer(f"❌ Время {time_input} недоступно. Выберите из доступных времен:", reply_markup=keyboard)
        return

    await state.update_data(appointment_time=time_input)

    # Переходим к выбору услуги
    services_text = format_services_text()
    keyboard = get_services_keyboard()
    await message.answer(services_text, reply_markup=keyboard)


async def handle_client_service_input(message: Message, state: FSMContext):
    """Обрабатывает ввод услуги клиента (если введено вручную)"""
    service = message.text.strip()

    # Проверяем, есть ли такая услуга в списке
    if service not in SERVICES:
        available_services = ", ".join(SERVICES.keys())
        keyboard = get_cancel_operation_keyboard("client", "booking")
        await message.answer(f"❌ Услуга не найдена. Доступные услуги: {available_services}", reply_markup=keyboard)
        return

    await state.update_data(service=service)

    # Показываем подтверждение
    booking_data = await state.get_data()
    confirmation_text = format_booking_confirmation(
        booking_data['client_name'],
        booking_data['appointment_date'],
        booking_data['appointment_time'],
        service
    )
    keyboard = get_appointment_confirmation_keyboard()
    await message.answer(confirmation_text, reply_markup=keyboard)


async def handle_client_reschedule_selection(message: Message, state: FSMContext):
    """Обрабатывает выбор записи для переноса"""
    appointment_id = message.text.strip()

    if not appointment_id.isdigit():
        await message.answer("❌ Введите корректный ID записи (число)")
        return

    # Проверяем, существует ли запись и принадлежит ли она пользователю
    appointment_info = get_appointment_by_id(int(appointment_id))

    if not appointment_info:
        await message.answer("❌ Запись не найдена")
        return

    client_name, appointment_date, appointment_time, service, telegram_user_id = appointment_info

    if telegram_user_id != message.from_user.id:
        await message.answer("❌ Это не ваша запись")
        return

    await state.update_data(reschedule_appointment_id=appointment_id)
    await message.answer("📅 Введите новую дату (ДД.ММ.ГГГГ):")
    await state.set_state(ClientRescheduleStates.waiting_for_new_date)


async def handle_client_reschedule_date(message: Message, state: FSMContext):
    """Обрабатывает ввод новой даты для переноса"""
    date_input = message.text.strip()

    if not validate_date_format(date_input):
        await message.answer(COMMON_MESSAGES['date_format_error'])
        return

    try:
        target_date = datetime.strptime(date_input, '%d.%m.%Y').date()
        today = datetime.now().date()

        if target_date < today:
            await message.answer("❌ Нельзя перенести на прошедшую дату")
            return

        data = await state.get_data()
        appointment_id = data.get('reschedule_appointment_id')

        # Получаем доступное время (исключая текущую запись)
        available_times = get_available_times(date_input, int(appointment_id))

        if not available_times:
            await message.answer(CLIENT_MESSAGES['no_available_times'])
            return

        await state.update_data(new_date=target_date.strftime('%Y-%m-%d'))

        times_text = format_available_times_text(available_times, date_input)
        keyboard = get_available_times_keyboard(available_times, date_input)
        await message.answer(times_text, reply_markup=keyboard)
        await state.set_state(ClientRescheduleStates.waiting_for_new_time)

    except ValueError:
        await message.answer(COMMON_MESSAGES['error_processing_date'])


async def handle_client_reschedule_time(message: Message, state: FSMContext):
    """Обрабатывает ввод нового времени для переноса"""
    time_input = message.text.strip()

    if not validate_time_format(time_input):
        await message.answer(COMMON_MESSAGES['time_format_error'])
        return

    data = await state.get_data()
    appointment_id = int(data.get('reschedule_appointment_id'))
    new_date = data.get('new_date')
    user_id = message.from_user.id

    # Получаем информацию о старой записи
    old_appointment = get_appointment_by_id(appointment_id)
    if not old_appointment:
        await message.answer(COMMON_MESSAGES['appointment_not_found'])
        await state.clear()
        return

    client_name, old_date, old_time, service, _ = old_appointment

    # Проверяем доступность нового времени
    date_str = datetime.strptime(new_date, '%Y-%m-%d').strftime('%d.%m.%Y')
    available_times = get_available_times(date_str, appointment_id)

    if time_input not in available_times:
        await message.answer(f"❌ Время {time_input} недоступно")
        return

    # Переносим запись
    if reschedule_appointment(appointment_id, new_date, time_input, user_id):
        success_text = format_reschedule_success(
            appointment_id, client_name, old_date, old_time,
            new_date, time_input, service
        )
        await message.answer(success_text)
    else:
        await message.answer("❌ Ошибка при переносе записи")

    await state.clear()


async def handle_client_cancel_selection(message: Message, state: FSMContext):
    """Обрабатывает выбор записи для отмены"""
    appointment_id = message.text.strip()

    if not appointment_id.isdigit():
        await message.answer("❌ Введите корректный ID записи (число)")
        return

    user_id = message.from_user.id
    appointment_info = get_appointment_by_id(int(appointment_id))

    if not appointment_info:
        await message.answer("❌ Запись не найдена")
        return

    client_name, appointment_date, appointment_time, service, telegram_user_id = appointment_info

    if telegram_user_id != user_id:
        await message.answer("❌ Это не ваша запись")
        return

    # Показываем подтверждение отмены
    confirmation_text = format_cancel_confirmation_client(
        int(appointment_id), client_name, appointment_date, appointment_time, service
    )
    keyboard = get_cancel_confirmation_keyboard(appointment_id)

    await message.answer(confirmation_text, reply_markup=keyboard)
    await state.clear()


async def start_reschedule_process(message: Message, state: FSMContext, appointment_id: str, user_id: int,
                                   edit: bool = False):
    """Начинает процесс переноса конкретной записи"""
    appointment_info = get_appointment_by_id(int(appointment_id))

    if not appointment_info or appointment_info[4] != user_id:
        text = "❌ Запись не найдена или не принадлежит вам"
        if edit:
            await message.edit_text(text)
        else:
            await message.answer(text)
        return

    await state.update_data(reschedule_appointment_id=appointment_id)
    text = "📅 Введите новую дату (ДД.ММ.ГГГГ):"

    if edit:
        await message.edit_text(text)
    else:
        await message.answer(text)

    await state.set_state(ClientRescheduleStates.waiting_for_new_date)


async def start_cancel_process(message: Message, state: FSMContext, appointment_id: str, user_id: int,
                               edit: bool = False):
    """Начинает процесс отмены конкретной записи"""
    appointment_info = get_appointment_by_id(int(appointment_id))

    if not appointment_info or appointment_info[4] != user_id:
        text = "❌ Запись не найдена или не принадлежит вам"
        if edit:
            await message.edit_text(text)
        else:
            await message.answer(text)
        return

    client_name, appointment_date, appointment_time, service, _ = appointment_info

    confirmation_text = format_cancel_confirmation_client(
        int(appointment_id), client_name, appointment_date, appointment_time, service
    )
    keyboard = get_cancel_confirmation_keyboard(appointment_id)

    if edit:
        await message.edit_text(confirmation_text, reply_markup=keyboard)
    else:
        await message.answer(confirmation_text, reply_markup=keyboard)


async def show_appointment_details(message: Message, appointment_id: str, edit: bool = False):
    """Показывает детали записи"""
    appointment_info = get_appointment_by_id(int(appointment_id))

    if not appointment_info:
        text = COMMON_MESSAGES['appointment_not_found']
        if edit:
            await message.edit_text(text)
        else:
            await message.answer(text)
        return

    client_name, appointment_date, appointment_time, service, _ = appointment_info
    details_text = format_appointment_details(
        int(appointment_id), client_name, appointment_date, appointment_time, service
    )
    keyboard = get_client_appointment_actions_keyboard(appointment_id)

    if edit:
        await message.edit_text(details_text, reply_markup=keyboard)
    else:
        await message.answer(details_text, reply_markup=keyboard)