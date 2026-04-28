"""Callback handler for medication intake actions from reminder messages."""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

import httpx
from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.config import settings

logger = logging.getLogger(__name__)
router = Router()


async def _get_user_by_telegram_id(telegram_id: int) -> dict[str, Any] | None:
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(f"{settings.API_BASE_URL}/users/{telegram_id}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()


@router.callback_query(F.data.startswith("intake_"))
async def handle_intake_callback(callback: CallbackQuery) -> None:
    if not callback.data:
        await callback.answer("Invalid action", show_alert=True)
        return

    try:
        action_part, medication_id, schedule_id, scheduled_date, scheduled_time = callback.data.split(":", 4)
        action = action_part.removeprefix("intake_")
        if action not in {"consumed", "not_consumed", "felt_bad"}:
            raise ValueError("invalid action")
    except Exception:
        await callback.answer("Invalid callback payload", show_alert=True)
        return

    if not callback.from_user:
        await callback.answer("Missing user", show_alert=True)
        return

    user = await _get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("You must register first.", show_alert=True)
        return

    status_map = {
        "consumed": "consumed",
        "not_consumed": "not_consumed",
        "felt_bad": "felt_bad",
    }
    response_text = {
        "consumed": "✅ Marked as taken. Great job!",
        "not_consumed": "❌ Noted. Try not to skip doses!",
        "felt_bad": "😟 Got it. Your supervisor has been notified.",
    }[action]

    payload = {
        "user_id": user["id"],
        "medication_id": int(medication_id),
        "schedule_id": int(schedule_id),
        "scheduled_time": scheduled_time,
        "scheduled_date": scheduled_date,
        "status": status_map[action],
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.post(f"{settings.API_BASE_URL}/intake-logs", json=payload)
            resp.raise_for_status()
        except Exception as exc:
            logger.error("Failed to log intake: %s", exc)
            await callback.answer("Failed to log intake", show_alert=True)
            return

    if callback.message:
        try:
            await callback.message.edit_text(response_text)
        except Exception:
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass

    await callback.answer()
