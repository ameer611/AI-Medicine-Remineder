"""Web login deep-link handler for /start web_<session_id>."""
from __future__ import annotations

import logging
from typing import Any

import httpx
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import settings
from bot.keyboards import request_contact_keyboard
from bot.states import RegistrationFlow

logger = logging.getLogger(__name__)
router = Router()


async def _get_user_by_telegram_id(telegram_id: int) -> dict[str, Any] | None:
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.get(f"{settings.API_BASE_URL}/users/{telegram_id}")
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.error("Failed to fetch user by telegram_id=%s: %s", telegram_id, exc)
            return None


async def _link_web_session(session_id: str, telegram_id: int) -> bool:
    if not settings.INTERNAL_API_KEY:
        return False
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            f"{settings.API_BASE_URL}/auth/bot-link",
            json={"session_id": session_id, "telegram_id": telegram_id},
            headers={"X-Internal-Key": settings.INTERNAL_API_KEY},
        )
        resp.raise_for_status()
        return True


@router.message(F.text.startswith("/start web_"))
async def cmd_start_web(message: Message, state: FSMContext) -> None:
    await state.clear()
    telegram_id = message.chat.id
    parts = message.text.split(maxsplit=1) if message.text else []
    if len(parts) < 2:
        await message.answer("❌ Invalid web login link.")
        return

    session_id = parts[1].removeprefix("web_")
    await state.update_data(web_session_id=session_id, registration_role="user")

    user = await _get_user_by_telegram_id(telegram_id)
    if user:
        try:
            await _link_web_session(session_id, telegram_id)
            await message.answer("✅ You are now logged in to the web app. You can return to the browser.")
        except Exception:
            await message.answer("⚠️ Could not complete web login. Please try again from the browser.")
        return

    await state.set_state(RegistrationFlow.waiting_for_phone)
    await message.answer(
        "👋 Welcome! To complete web login, please share your phone number first.",
        reply_markup=request_contact_keyboard(),
    )
