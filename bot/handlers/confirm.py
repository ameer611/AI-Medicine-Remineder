"""Confirmation handler."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.handlers.utils import medication_card
from bot.keyboards import field_keyboard, times_keyboard
from bot.states import PrescriptionFlow

router = Router()


@router.callback_query(PrescriptionFlow.confirming_medication, F.data == "confirm")
async def on_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    medications: list[dict] = data["medications"]
    idx: int = data["current_index"]
    med = medications[idx]

    # Initialize time selection array for this med
    await state.update_data(selected_times=[])
    await state.set_state(PrescriptionFlow.selecting_times)
    
    await callback.message.edit_text(  # type: ignore
        f"✅ Confirmed <b>{med['name']}</b>.\n\n"
        f"You need to select <b>{med['dosage_per_day']}</b> time(s) to take this medication:",
        reply_markup=times_keyboard([], med["dosage_per_day"]),
    )
    await callback.answer()


@router.callback_query(PrescriptionFlow.confirming_medication, F.data == "edit")
async def on_edit(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    medications: list[dict] = data["medications"]
    idx: int = data["current_index"]
    med = medications[idx]

    await state.set_state(PrescriptionFlow.editing_field_choice)
    await callback.message.edit_text(  # type: ignore
        f"✏️ What do you want to edit for <b>{med['name']}</b>?",
        reply_markup=field_keyboard(),
    )
    await callback.answer()
