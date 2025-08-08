from aiogram.fsm.state import State, StatesGroup


# ===== СОСТОЯНИЯ ДЛЯ АДМИНИСТРАТОРА =====

class AdminEditStates(StatesGroup):
    """Состояния для редактирования записей (админ)"""
    waiting_for_search = State()
    waiting_for_new_time = State()
    waiting_for_new_client = State()
    waiting_for_new_service = State()
    waiting_for_date = State()


class AdminAddStates(StatesGroup):
    """Состояния для добавления записи (админ)"""
    waiting_for_client_name = State()
    waiting_for_appointment_date = State()
    waiting_for_appointment_time = State()
    waiting_for_service = State()
    confirmation = State()


# ===== СОСТОЯНИЯ ДЛЯ КЛИЕНТОВ =====

class ClientBookingStates(StatesGroup):
    """Состояния для записи клиента"""
    waiting_for_name = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_service = State()
    confirmation = State()


class ClientRescheduleStates(StatesGroup):
    """Состояния для переноса записи клиента"""
    waiting_for_appointment_selection = State()
    waiting_for_new_date = State()
    waiting_for_new_time = State()
    confirmation = State()


class ClientCancelStates(StatesGroup):
    """Состояния для отмены записи клиента"""
    waiting_for_appointment_selection = State()
    confirmation = State()