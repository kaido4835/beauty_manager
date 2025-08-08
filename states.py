from aiogram.fsm.state import State, StatesGroup


class EditStates(StatesGroup):
    """Состояния для редактирования записей"""
    waiting_for_search = State()
    waiting_for_new_time = State()
    waiting_for_date = State()


class AddAppointmentStates(StatesGroup):
    """Состояния для добавления новой записи"""
    waiting_for_client_name = State()
    waiting_for_appointment_date = State()
    waiting_for_appointment_time = State()
    waiting_for_service = State()
    confirmation = State()