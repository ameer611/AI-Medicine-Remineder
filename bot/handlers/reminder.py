"""Reminder handling — offset selection, duration selection, and scheduler logic."""
import logging
from typing import Any

import httpx
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.utils import medication_card
from bot.keyboards import confirm_keyboard, duration_keyboard
from bot.states import PrescriptionFlow
from app.config import settings

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(PrescriptionFlow.selecting_reminder_offset, F.data.startswith("offset:"))
async def on_offset_choice(callback: CallbackQuery, state: FSMContext) -> None:
    offset = int(callback.data.split(":")[1])
    await state.update_data(reminder_offset_minutes=offset)
    
    data = await state.get_data()
    medications: list[dict] = data["medications"]
    idx: int = data["current_index"]
    med: dict[str, Any] = medications[idx]

    if med.get("duration_in_days"):
        await _finalize_medication(callback.message, state, med["duration_in_days"])  # type: ignore
        await callback.answer()
        return

    await state.set_state(PrescriptionFlow.selecting_duration)
    await callback.message.edit_text(  # type: ignore
        f"⏳ You chose a reminder **{offset} minutes** before intake.\n\n"
        "For how many days should we run this reminder schedule?",
        reply_markup=duration_keyboard(),
    )
    await callback.answer()


@router.callback_query(PrescriptionFlow.selecting_duration, F.data.startswith("duration:"))
async def on_duration_choice(callback: CallbackQuery, state: FSMContext) -> None:
    action = callback.data.split(":")[1]
    
    if action == "other":
        await callback.message.answer(  # type: ignore
            "⌨️ Please type the number of days (e.g., 10, 21):"
        )
        return
        
    duration = int(action)
    await _finalize_medication(callback.message, state, duration)  # type: ignore
    await callback.answer()


@router.message(PrescriptionFlow.selecting_duration)
async def on_custom_duration(message: Message, state: FSMContext) -> None:
    text = message.text.strip() if message.text else ""
    try:
        duration = int(text)
        if duration <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Please enter a valid positive number of days.")
        return
        
    await _finalize_medication(message, state, duration)


async def _finalize_medication(message: Message, state: FSMContext, duration: int) -> None:
    data = await state.get_data()
    medications: list[dict] = data["medications"]
    idx: int = data["current_index"]
    med: dict[str, Any] = medications[idx]
    
    selected_times: list[str] = data["selected_times"]
    offset: int = data["reminder_offset_minutes"]
    
    user_id = message.chat.id
    
    try:
        await message.delete()
    except Exception:
        pass

    # 1. Save to database via API
    payload = {
        "telegram_id": user_id,
        "medication": {
            "name": med["name"],
            "user_id": 0,
            "dosage_per_day": med["dosage_per_day"],
            "timing": med.get("timing", "custom"),
            "notes": med.get("notes"),
        },
        "times": selected_times,
        "reminder_offset_minutes": offset,
        "duration_in_days": duration,
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(f"{settings.API_BASE_URL}/medications", json=payload)
            resp.raise_for_status()
            response_data = resp.json()
        except Exception as exc:
            logger.error("Failed to save medication: %s", exc)
            await message.answer("❌ Failed to save schedule to database. Please try again later.")
            return

    # 2. Schedule APScheduler jobs automatically inside FastAPI via internal imports?
    # Wait, the scheduler runs inside the bot process, so we schedule it here directly.
    from app.services.scheduler_service import schedule_reminders
    try:
        schedules = response_data.get("schedules", [])
        schedule_reminders(
            bot_token=settings.BOT_TOKEN,
            chat_id=user_id,
            medication_id=response_data["medication"]["id"],
            schedules=schedules,
            med_name=med["name"],
            notes=med.get("notes"),
            offset_minutes=offset,
            duration_days=duration,
        )
    except Exception as exc:
        logger.error("Failed to schedule reminders: %s", exc)
        await message.answer("❌ Failed to add reminders to the scheduler.")
        return

    # 3. Confirm success
    times_str = ", ".join(selected_times)
    await message.answer(
        f"✅ <b>Successfully Scheduled!</b>\n\n"
        f"💊 <b>{med['name']}</b>\n"
        f"⏰ Times: {times_str}\n"
        f"🔔 Reminder: {offset} min before\n"
        f"📅 Duration: {duration} days"
    )

    # 4. Process next medication if any
    idx += 1
    if idx < len(medications):
        await state.update_data(current_index=idx)
        await state.set_state(PrescriptionFlow.confirming_medication)
        next_med = medications[idx]
        await message.answer(
            f"Let's configure the next one:\n\n" +
            medication_card(next_med, idx, len(medications)),
            reply_markup=confirm_keyboard(),
        )
    else:
        await state.clear()
        
        # We need the new keyboard imported here, but we can just inline import it
        from bot.keyboards import view_schedules_keyboard
        
        await message.answer(
            "🎉 All medications from the prescription have been scheduled!\n"
            "You will receive reminders automatically.",
            reply_markup=view_schedules_keyboard()
        )
