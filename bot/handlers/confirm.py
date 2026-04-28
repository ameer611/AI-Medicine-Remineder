"""Confirmation handler."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.handlers.utils import medication_card
from bot.keyboards import field_keyboard, times_keyboard, confirm_or_customize_times_keyboard, offset_keyboard
from bot.states import PrescriptionFlow

router = Router()


@router.callback_query(PrescriptionFlow.confirming_medication, F.data == "confirm")
async def on_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    medications: list[dict] = data["medications"]
    idx: int = data["current_index"]
    med = medications[idx]

    suggested_times: list[str] = med.get("suggested_times") or []
    if suggested_times and len(suggested_times) == med["dosage_per_day"]:
        await state.update_data(selected_times=suggested_times)
        await callback.message.edit_text(  # type: ignore
            f"💡 <b>Suggested schedule for {med['name']}:</b>\n\n"
            + "\n".join([f"📍 {time}" for time in suggested_times])
            + (
                f"\n\nReason: {med.get('timing_reasoning') or '—'}"
            ),
            reply_markup=confirm_or_customize_times_keyboard(),
        )
        await callback.answer()
        return

    # Initialize time selection array for this med
    await state.update_data(selected_times=[])
    await state.set_state(PrescriptionFlow.selecting_times)
    
    await callback.message.edit_text(  # type: ignore
        f"✅ Confirmed <b>{med['name']}</b>.\n\n"
        f"You need to select <b>{med['dosage_per_day']}</b> time(s) to take this medication:",
        reply_markup=times_keyboard([], med["dosage_per_day"]),
    )
    await callback.answer()


@router.callback_query(F.data == "times:use_suggested")
async def on_use_suggested_times(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    medications: list[dict] = data["medications"]
    idx: int = data["current_index"]
    med = medications[idx]
    selected_times: list[str] = med.get("suggested_times") or data.get("selected_times", [])

    await state.update_data(selected_times=selected_times)
    await state.set_state(PrescriptionFlow.selecting_reminder_offset)
    await callback.message.edit_text(  # type: ignore
        "🔔 How many minutes before the intake time do you want a reminder?",
        reply_markup=offset_keyboard(),
    )
    # The existing offset keyboard will be shown by the next step; keep response simple here.
    await callback.answer()


@router.callback_query(F.data == "times:customize")
async def on_customize_times(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    medications: list[dict] = data["medications"]
    idx: int = data["current_index"]
    med = medications[idx]
    await state.update_data(selected_times=[])
    await state.set_state(PrescriptionFlow.selecting_times)
    await callback.message.edit_text(  # type: ignore
        f"✏️ Please choose custom times for <b>{med['name']}</b>:\n\n"
        f"You need exactly {med['dosage_per_day']} time(s).",
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
