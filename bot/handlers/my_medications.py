"""Handler for /my_medications — shows active medication schedules."""
import logging
from typing import Any

import httpx
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.config import settings

logger = logging.getLogger(__name__)
router = Router()


def _format_medication(med: dict[str, Any]) -> str:
    times = med.get("times") or []
    times_str = ", ".join(times) if times else "—"
    return (
        f"💊 <b>{med['name']}</b>\n"
        f"📊 Dosage: {med['dosage_per_day']} time(s)/day\n"
        f"🕒 Times: {times_str}\n"
        f"🔔 Reminder: {med['reminder_offset_minutes']} min before"
    )


@router.message(Command("my_medications"))
async def cmd_my_medications(message: Message) -> None:
    telegram_id = message.chat.id

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(
                f"{settings.API_BASE_URL}/medications/{telegram_id}/active"
            )
            if resp.status_code == 404:
                await message.answer("You don't have any medications configured yet.")
                return
            resp.raise_for_status()
        except Exception as exc:
            logger.error("Failed to fetch active medications: %s", exc)
            await message.answer("❌ Failed to fetch your medications. Please try again later.")
            return

    data = resp.json()
    meds = data.get("medications", [])
    if not meds:
        await message.answer("You don't have any active medication reminders yet.")
        return

    parts = [_format_medication(m) for m in meds]
    text = "📋 <b>Your active medications</b>:\n\n" + "\n\n".join(parts)
    await message.answer(text)


@router.callback_query(F.data == "view_my_medications")
async def on_view_my_medications_callback(callback: CallbackQuery) -> None:
    if isinstance(callback.message, Message):
        await cmd_my_medications(callback.message)
    await callback.answer()

