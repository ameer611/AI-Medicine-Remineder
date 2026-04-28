"""Aiogram FSM state groups for the prescription flow."""
from aiogram.fsm.state import State, StatesGroup


class PrescriptionFlow(StatesGroup):
    waiting_for_entry_method = State()
    waiting_for_image = State()
    confirming_medication = State()
    editing_field_choice = State()
    editing_field_value = State()
    selecting_times = State()
    selecting_reminder_offset = State()
    selecting_duration = State()


class RegistrationFlow(StatesGroup):
    waiting_for_phone = State()
    waiting_for_supervisor_selection = State()


class SupervisorRegistrationFlow(StatesGroup):
    waiting_for_phone = State()


class WebAuthFlow(StatesGroup):
    waiting_for_phone = State()
