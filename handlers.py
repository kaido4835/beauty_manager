from datetime import datetime
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import MESSAGES
from database import (
    get_schedule, get_schedule_by_date, get_schedule_by_specific_date,
    search_appointment, delete_appointment, update_appointment_time,
    check_time_conflict, get_appointment_by_id, add_appointment, get_stats_summary
)
from keyboards import (
    get_main_menu_keyboard, get_schedule_navigation_keyboard,
    get_appointment_actions_keyboard, get_delete_confirmation_keyboard,
    get_edit_schedule_keyboard, get_selected_date_keyboard,
    get_add_appointment_confirmation_keyboard, get_cancel_add_keyboard,
    get_main_menu_inline_keyboard
)
from utils import (
    format_date_russian, validate_time_format, validate_date_format,
    format_schedule_text, format_appointment_info, format_multiple_appointments,
    format_delete_confirmation, format_time_change_success, format_delete_success,
    format_time_conflict, format_appointment_confirmation, format_appointment_success,
    validate_client_name, validate_service_name
)
from states import EditStates, AddAppointmentStates

# Создаем роутер для обработчиков
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    # Получаем статистику для приветствия
    stats = get_stats_summary()

    # Формируем приветственное сообщение
    welcome_text = (
        "Привет! 👋\n\n"
        "Я — бот, который поможет тебе больше не забывать про записи клиентов и сэкономить кучу времени.\n\n"
        "Вот что я умею:\n"
        "✅ Показывать записи на день\n"
        "✅ Напоминать о клиентах заранее\n"
        "✅ Удобно вести график прямо в Telegram\n\n"
        f"📊 Сегодня у вас: {stats['today']} записей\n\n"
        "Выберите действие или используйте кнопки ниже ⬇️"
    )

    # Отправляем только основную клавиатуру
    main_keyboard = get_main_menu_keyboard()
    await message.answer(welcome_text, reply_markup=main_keyboard)


@router.callback_query()
async def handle_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик всех callback запросов"""

    # Редактирование расписания
    if callback.data == "edit_schedule":
        await callback.message.answer(MESSAGES['search_prompt'])
        await state.set_state(EditStates.waiting_for_search)

    # Выбор даты
    elif callback.data == "select_date":
        await callback.message.answer(MESSAGES['date_prompt'])
        await state.set_state(EditStates.waiting_for_date)

    # Навигация по дням
    elif callback.data.startswith("next_day_"):
        day_offset = int(callback.data.replace("next_day_", ""))
        appointments, target_date = get_schedule_by_date(day_offset)

        schedule_text = format_schedule_text(appointments, target_date)
        keyboard = get_schedule_navigation_keyboard(day_offset)

        await callback.message.edit_text(schedule_text, reply_markup=keyboard)

    # Изменение времени записи
    elif callback.data.startswith("time_"):
        appointment_id = callback.data.replace("time_", "")
        await state.update_data(appointment_id=appointment_id)

        await callback.message.edit_text(MESSAGES['time_prompt'])
        await state.set_state(EditStates.waiting_for_new_time)

    # Удаление записи
    elif callback.data.startswith("delete_"):
        appointment_id = callback.data.replace("delete_", "")
        appointment_info = get_appointment_by_id(appointment_id)

        if appointment_info:
            client_name, appointment_date, appointment_time, service = appointment_info
            confirmation_text = format_delete_confirmation(
                client_name, appointment_date, appointment_time, service
            )
            keyboard = get_delete_confirmation_keyboard(appointment_id)

            await callback.message.edit_text(confirmation_text, reply_markup=keyboard)
        else:
            await callback.message.edit_text(MESSAGES['appointment_not_found'])

    # Подтверждение удаления
    elif callback.data.startswith("confirm_delete_"):
        appointment_id = callback.data.replace("confirm_delete_", "")
        appointment_info = get_appointment_by_id(appointment_id)

        if appointment_info:
            client_name, appointment_date, appointment_time, _ = appointment_info
            delete_appointment(appointment_id)

            success_text = format_delete_success(client_name, appointment_date, appointment_time)
            await callback.message.edit_text(success_text)
        else:
            await callback.message.edit_text(MESSAGES['appointment_not_found'])

        await state.clear()

    # Подтверждение добавления записи
    elif callback.data == "confirm_add_appointment":
        data = await state.get_data()
        client_name = data.get('client_name')
        appointment_date = data.get('appointment_date')
        appointment_time = data.get('appointment_time')
        service = data.get('service')

        # Добавляем запись в базу данных
        appointment_id = add_appointment(client_name, appointment_date, appointment_time, service)

        success_text = format_appointment_success(
            client_name, appointment_date, appointment_time, service, appointment_id
        )

        await callback.message.edit_text(success_text)
        await state.clear()

    # Отмена добавления записи
    elif callback.data == "cancel_add_appointment":
        await callback.message.edit_text(MESSAGES['appointment_cancelled'])
        await state.clear()

    # Возврат в главное меню
    elif callback.data == "main_menu":
        # Очищаем состояние
        await state.clear()

        # Получаем статистику для главного меню
        stats = get_stats_summary()

        # Формируем сообщение
        welcome_text = (
            "🏠 Главное меню\n\n"
            "Добро пожаловать в систему управления записями!\n\n"
            f"📊 Быстрая статистика:\n"
            f"📅 Сегодня: {stats['today']} записей\n\n"
            "Выберите действие или используйте кнопки ниже ⬇️"
        )

        # Удаляем предыдущее сообщение если возможно
        try:
            await callback.message.delete()
        except:
            pass  # Игнорируем ошибку если сообщение уже удалено

        # Отправляем только основную клавиатуру
        main_keyboard = get_main_menu_keyboard()
        await callback.message.answer(welcome_text, reply_markup=main_keyboard)

    # Быстрый просмотр расписания на сегодня
    elif callback.data == "schedule_today":
        appointments = get_schedule()
        today = datetime.now().date()

        schedule_text = format_schedule_text(appointments, today)
        keyboard = get_schedule_navigation_keyboard(0)

        await callback.message.edit_text(schedule_text, reply_markup=keyboard)

    # Быстрый просмотр расписания на завтра
    elif callback.data == "schedule_tomorrow":
        appointments, tomorrow = get_schedule_by_date(1)

        schedule_text = format_schedule_text(appointments, tomorrow)
        keyboard = get_schedule_navigation_keyboard(1)

        await callback.message.edit_text(schedule_text, reply_markup=keyboard)

    # Быстрый поиск
    elif callback.data == "quick_search":
        await callback.message.edit_text(MESSAGES['search_feature'])
        await state.set_state(EditStates.waiting_for_search)

    # Отмена удаления
    elif callback.data == "cancel_delete":
        await callback.message.edit_text(MESSAGES['delete_cancelled'])
        await state.clear()

    await callback.answer()


@router.message()
async def handle_message(message: Message, state: FSMContext):
    """Обработчик всех текстовых сообщений"""
    current_state = await state.get_state()

    # Обработка состояния поиска записи для редактирования
    if current_state == EditStates.waiting_for_search:
        search_term = message.text.strip()
        appointments = search_appointment(search_term)

        if not appointments:
            await message.answer(MESSAGES['not_found'])
            return

        if len(appointments) == 1:
            # Найдена одна запись - показываем варианты действий
            appointment_id, client_name, appointment_date, appointment_time, service = appointments[0]

            info_text = format_appointment_info(
                appointment_id, client_name, appointment_date, appointment_time, service
            )
            keyboard = get_appointment_actions_keyboard(appointment_id)

            await message.answer(info_text, reply_markup=keyboard)
        else:
            # Найдено несколько записей - показываем список
            result_text = format_multiple_appointments(appointments)
            await message.answer(result_text)

        await state.clear()

    # Обработка изменения времени
    elif current_state == EditStates.waiting_for_new_time:
        new_time = message.text.strip()
        data = await state.get_data()
        appointment_id = data.get('appointment_id')

        # Проверяем формат времени
        if not validate_time_format(new_time):
            await message.answer(MESSAGES['time_format_error'])
            return  # Не очищаем состояние, ждем корректный ввод

        # Получаем информацию о записи
        appointment_info = get_appointment_by_id(appointment_id)

        if appointment_info:
            old_client_name, appointment_date, old_time, service = appointment_info
            date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            formatted_date = format_date_russian(date_obj)

            # Проверяем конфликт времени
            conflict = check_time_conflict(new_time, appointment_date, appointment_id)

            if conflict:
                conflict_text = format_time_conflict(new_time, formatted_date, conflict[0])
                await message.answer(conflict_text)
            else:
                # Обновляем время
                update_appointment_time(appointment_id, new_time)

                success_text = format_time_change_success(
                    old_client_name, appointment_date, old_time, new_time, service
                )
                await message.answer(success_text)
        else:
            await message.answer(MESSAGES['appointment_not_found'])

        await state.clear()

    # Обработка ввода даты
    elif current_state == EditStates.waiting_for_date:
        date_input = message.text.strip()

        # Проверяем формат даты
        if not validate_date_format(date_input):
            await message.answer(MESSAGES['date_format_error'])
            return  # Не очищаем состояние, ждем корректный ввод

        # Получаем расписание на указанную дату
        appointments, target_date = get_schedule_by_specific_date(date_input)

        if target_date is None:
            await message.answer(MESSAGES['error_processing_date'])
            return

        # Выводим результат с полным функционалом
        schedule_text = format_schedule_text(appointments, target_date)

        # Создаем клавиатуру с возможностью редактирования и выбора другой даты
        keyboard = get_selected_date_keyboard()

        await message.answer(schedule_text, reply_markup=keyboard)
        await state.clear()

    # === ОБРАБОТКА ДОБАВЛЕНИЯ ЗАПИСИ ===

    # Ожидание имени клиента
    elif current_state == AddAppointmentStates.waiting_for_client_name:
        client_name = message.text.strip()

        if not validate_client_name(client_name):
            keyboard = get_cancel_add_keyboard()
            await message.answer(MESSAGES['invalid_client_name'], reply_markup=keyboard)
            return

        # Сохраняем имя клиента и переходим к вводу даты
        await state.update_data(client_name=client_name)
        keyboard = get_cancel_add_keyboard()
        await message.answer(MESSAGES['add_appointment_date'], reply_markup=keyboard)
        await state.set_state(AddAppointmentStates.waiting_for_appointment_date)

    # Ожидание даты записи
    elif current_state == AddAppointmentStates.waiting_for_appointment_date:
        date_input = message.text.strip()

        if not validate_date_format(date_input):
            keyboard = get_cancel_add_keyboard()
            await message.answer(MESSAGES['date_format_error'], reply_markup=keyboard)
            return

        # Преобразуем дату в формат базы данных
        try:
            appointment_date = datetime.strptime(date_input, '%d.%m.%Y').date().strftime('%Y-%m-%d')
            await state.update_data(appointment_date=appointment_date)

            keyboard = get_cancel_add_keyboard()
            await message.answer(MESSAGES['add_appointment_time'], reply_markup=keyboard)
            await state.set_state(AddAppointmentStates.waiting_for_appointment_time)
        except ValueError:
            keyboard = get_cancel_add_keyboard()
            await message.answer(MESSAGES['error_processing_date'], reply_markup=keyboard)

    # Ожидание времени записи
    elif current_state == AddAppointmentStates.waiting_for_appointment_time:
        time_input = message.text.strip()

        if not validate_time_format(time_input):
            keyboard = get_cancel_add_keyboard()
            await message.answer(MESSAGES['time_format_error'], reply_markup=keyboard)
            return

        # Проверяем конфликт времени
        data = await state.get_data()
        appointment_date = data.get('appointment_date')

        conflict = check_time_conflict(time_input, appointment_date)
        if conflict:
            date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            formatted_date = format_date_russian(date_obj)
            conflict_text = format_time_conflict(time_input, formatted_date, conflict[0])

            keyboard = get_cancel_add_keyboard()
            await message.answer(conflict_text, reply_markup=keyboard)
            return

        # Сохраняем время и переходим к вводу услуги
        await state.update_data(appointment_time=time_input)
        keyboard = get_cancel_add_keyboard()
        await message.answer(MESSAGES['add_service'], reply_markup=keyboard)
        await state.set_state(AddAppointmentStates.waiting_for_service)

    # Ожидание названия услуги
    elif current_state == AddAppointmentStates.waiting_for_service:
        service = message.text.strip()

        if not validate_service_name(service):
            keyboard = get_cancel_add_keyboard()
            await message.answer(MESSAGES['invalid_service'], reply_markup=keyboard)
            return

        # Сохраняем услугу и показываем подтверждение
        await state.update_data(service=service)

        data = await state.get_data()
        confirmation_text = format_appointment_confirmation(
            data['client_name'], data['appointment_date'],
            data['appointment_time'], service
        )

        keyboard = get_add_appointment_confirmation_keyboard()
        await message.answer(confirmation_text, reply_markup=keyboard)
        await state.set_state(AddAppointmentStates.confirmation)

    # === ОБЫЧНЫЕ КОМАНДЫ ===
    elif message.text == "📅 Посмотреть расписание":
        appointments = get_schedule()
        today = datetime.now().date()

        schedule_text = format_schedule_text(appointments, today)
        keyboard = get_schedule_navigation_keyboard(0)

        await message.answer(schedule_text, reply_markup=keyboard)

    elif message.text == "➕ Добавить запись":
        keyboard = get_cancel_add_keyboard()
        await message.answer(MESSAGES['add_feature'], reply_markup=keyboard)
        await state.set_state(AddAppointmentStates.waiting_for_client_name)

    elif message.text == "🔍 Найти запись":
        await message.answer(MESSAGES['search_prompt'])
        await state.set_state(EditStates.waiting_for_search)

    elif message.text == "📊 Статистика":
        stats = get_stats_summary()
        stats_text = MESSAGES['stats_message'].format(
            today=stats['today'],
            tomorrow=stats['tomorrow'],
            week=stats['week'],
            total=stats['total']
        )
        await message.answer(stats_text)

    else:
        if not current_state:  # Если не в состоянии редактирования
            await message.answer(MESSAGES['unknown_command'])