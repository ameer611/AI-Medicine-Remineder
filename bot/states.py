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
