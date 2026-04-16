"""Times handler — time selection logic."""
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import offset_keyboard, times_keyboard
from bot.states import PrescriptionFlow

router = Router()
HH_MM_RE = re.compile(r"^\d{2}:\d{2}$")


@router.callback_query(PrescriptionFlow.selecting_times, F.data.startswith("time:"))
async def on_time_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":", 1)
    if len(parts) < 2:
        return
    action = parts[1]

    data = await state.get_data()
    medications: list[dict] = data["medications"]
    idx: int = data["current_index"]
    req: int = medications[idx]["dosage_per_day"]
    selected: list[str] = data.get("selected_times", [])

    if action == "not_ready":
        await callback.answer(f"Please select exactly {req} time(s).", show_alert=True)
        return

    if action == "done":
        if len(selected) != req:
            await callback.answer(f"Select exactly {req} times.", show_alert=True)
            return

        # Advance to reminder offset selection
        await state.update_data(selected_times=sorted(selected))
        await state.set_state(PrescriptionFlow.selecting_reminder_offset)
        
        await callback.message.edit_text(  # type: ignore
            "🔔 How many minutes before the intake time do you want a reminder?",
            reply_markup=offset_keyboard(),
        )
        return

    if action == "other":
        await callback.message.answer(  # type: ignore
            "⌨️ Please type a custom time in HH:MM format (24-hour, e.g., 09:30 or 14:15):"
        )
        return

    # Toggle specific time
    if action in selected:
        selected.remove(action)
    else:
        if len(selected) < req:
            selected.append(action)
        else:
            await callback.answer(f"You can only select up to {req} time(s).", show_alert=True)
            return

    await state.update_data(selected_times=selected)
    await callback.message.edit_reply_markup(  # type: ignore
        reply_markup=times_keyboard(selected, req)
    )


@router.message(PrescriptionFlow.selecting_times)
async def on_custom_time(message: Message, state: FSMContext) -> None:
    text = message.text.strip() if message.text else ""
    if not HH_MM_RE.match(text):
        await message.answer("❌ Invalid format. Please use HH:MM (e.g. 09:30, 21:00).")
        return

    hh, mm = map(int, text.split(":"))
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        await message.answer("❌ Invalid time value. Hours 00-23, Minutes 00-59.")
        return

    data = await state.get_data()
    medications: list[dict] = data["medications"]
    idx: int = data["current_index"]
    req: int = medications[idx]["dosage_per_day"]
    selected: list[str] = data.get("selected_times", [])

    if len(selected) >= req:
        await message.answer(f"❌ You've already selected {req} times. Tap the grid above to unselect some.")
        return
    if text in selected:
        await message.answer("❌ This time is already selected.")
        return

    selected.append(text)
    await state.update_data(selected_times=selected)
    
    await message.answer(
        f"✅ Added {text} to your selected times.\n"
        "Continue selecting or press Done:",
        reply_markup=times_keyboard(selected, req)
    )
