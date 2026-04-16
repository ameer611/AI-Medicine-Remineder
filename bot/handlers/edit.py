"""Edit handler — manages updating a single field of a medication."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.utils import medication_card
from bot.keyboards import confirm_keyboard
from bot.states import PrescriptionFlow

router = Router()


@router.callback_query(PrescriptionFlow.editing_field_choice, F.data.startswith("field:"))
async def on_field_choice(callback: CallbackQuery, state: FSMContext) -> None:
    field = callback.data.split(":")[1]
    await state.update_data(editing_field=field)
    await state.set_state(PrescriptionFlow.editing_field_value)
    
    prompt_map = {
        "name": "Send the new name for the medication:",
        "dosage": "Send the new dosage (number of times per day, 1-4):",
        "timing": "Send the timing (e.g. morning, afternoon, evening, custom):",
        "notes": "Send any notes for this medication (e.g. after meal, before meal):",
        "duration": "Send the duration in days (e.g. 10):",
    }
    
    await callback.message.edit_text(prompt_map.get(field, "Send the new value:"))  # type: ignore
    await callback.answer()


@router.message(PrescriptionFlow.editing_field_value)
async def on_field_value(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    field: str = data["editing_field"]
    medications: list[dict] = data["medications"]
    idx: int = data["current_index"]
    med: dict = medications[idx]

    value = message.text.strip() if message.text else ""
    if not value:
        await message.answer("Please send text.")
        return

    # Basic validation
    if field == "dosage":
        try:
            val = int(value)
            if not (1 <= val <= 4):
                raise ValueError
            med["dosage_per_day"] = val
        except ValueError:
            await message.answer("❌ Dosage must be a number between 1 and 4. Try again:")
            return
    elif field == "name":
        med["name"] = value
    elif field == "timing":
        med["timing"] = value.lower()
    elif field == "notes":
        med["notes"] = value
    elif field == "duration":
        try:
            val = int(value)
            if val <= 0: raise ValueError
            med["duration_in_days"] = val
        except ValueError:
            await message.answer("❌ Duration must be a positive number of days. Try again:")
            return

    # Persist updated med to FSM
    medications[idx] = med
    await state.update_data(medications=medications)
    
    # Go back to confirming
    await state.set_state(PrescriptionFlow.confirming_medication)
    await message.answer(
        medication_card(med, idx, len(medications)),
        reply_markup=confirm_keyboard(),
    )
