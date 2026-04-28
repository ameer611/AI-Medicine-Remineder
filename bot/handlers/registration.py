"""Registration flow for users and supervisors."""
from __future__ import annotations

import logging
from typing import Any

import httpx
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Contact, Message, ReplyKeyboardRemove

from app.config import settings
from bot.keyboards import main_menu_keyboard, request_contact_keyboard, supervisor_selection_keyboard
from bot.states import RegistrationFlow, SupervisorRegistrationFlow

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


async def _get_supervisors() -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(f"{settings.API_BASE_URL}/users/supervisors")
        resp.raise_for_status()
        return resp.json()


async def _register_user(payload: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(f"{settings.API_BASE_URL}/users/register", json=payload)
        resp.raise_for_status()
        return resp.json()


async def _maybe_link_web_session(message: Message, telegram_id: int, state: FSMContext) -> None:
    data = await state.get_data()
    session_id = data.get("web_session_id")
    if not session_id:
        return
    if not settings.INTERNAL_API_KEY:
        logger.warning("INTERNAL_API_KEY missing; cannot link web session")
        return

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            f"{settings.API_BASE_URL}/auth/bot-link",
            json={"session_id": session_id, "telegram_id": telegram_id},
            headers={"X-Internal-Key": settings.INTERNAL_API_KEY},
        )
        resp.raise_for_status()


async def _finalize_web_login(telegram_id: int, state: FSMContext) -> None:
    data = await state.get_data()
    session_id = data.get("web_session_id")
    if not session_id or not settings.INTERNAL_API_KEY:
        return

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            f"{settings.API_BASE_URL}/auth/bot-link",
            json={"session_id": session_id, "telegram_id": telegram_id},
            headers={"X-Internal-Key": settings.INTERNAL_API_KEY},
        )
        resp.raise_for_status()
@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    telegram_id = message.chat.id

    user = await _get_user_by_telegram_id(telegram_id)
    if user:
        await message.answer(
            "👋 Welcome back!",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.set_state(RegistrationFlow.waiting_for_phone)
    await state.update_data(registration_role="user")
    await message.answer(
        "👋 Welcome to Dori Scheduler! Please share your phone number to register.",
        reply_markup=request_contact_keyboard(),
    )


@router.message(F.text.startswith("/start supervisor_"))
async def cmd_start_supervisor(message: Message, state: FSMContext) -> None:
    await state.clear()
    telegram_id = message.chat.id
    payload = message.text.split(maxsplit=1)[1] if message.text and len(message.text.split(maxsplit=1)) > 1 else ""
    code = payload.removeprefix("supervisor_")
    if not settings.SUPERVISOR_INVITE_CODE or code != settings.SUPERVISOR_INVITE_CODE:
        await message.answer("❌ Invalid supervisor invite code.")
        return

    user = await _get_user_by_telegram_id(telegram_id)
    if user:
        await message.answer("❌ This Telegram account is already registered.")
        return

    await state.set_state(SupervisorRegistrationFlow.waiting_for_phone)
    await state.update_data(registration_role="supervisor")
    await message.answer(
        "👋 Welcome, supervisor candidate. Please share your phone number to continue.",
        reply_markup=request_contact_keyboard(),
    )


@router.message(RegistrationFlow.waiting_for_phone, F.contact)
@router.message(SupervisorRegistrationFlow.waiting_for_phone, F.contact)
async def on_phone_received(message: Message, state: FSMContext) -> None:
    contact: Contact | None = message.contact
    if not contact:
        await message.answer("❌ Please use the phone sharing button.")
        return

    telegram_id = message.chat.id
    phone_number = contact.phone_number
    if not phone_number:
        await message.answer("❌ Could not read phone number. Please try again.")
        return

    data = await state.get_data()
    role = data.get("registration_role", "user")

    if role == "supervisor":
        full_name = message.from_user.full_name if message.from_user else "Supervisor"
        try:
            await _register_user({
                "telegram_id": telegram_id,
                "full_name": full_name,
                "phone_number": phone_number,
                "supervisor_id": None,
                "role": "supervisor",
            })
            await _finalize_web_login(telegram_id, state)
            await state.clear()
            await message.answer(
                f"✅ Registration complete! Welcome, {full_name}.",
                reply_markup=main_menu_keyboard(),
            )
        except Exception as exc:
            logger.error("Supervisor registration failed: %s", exc)
            await message.answer("❌ Registration failed. Please try again later.")
        return

    supervisors = await _get_supervisors()
    if not supervisors:
        await message.answer("❌ No supervisors are registered yet. Please try again later.")
        return

    await state.set_state(RegistrationFlow.waiting_for_supervisor_selection)
    await state.update_data(phone_number=phone_number)
    await message.answer(
        "Please choose your supervisor:",
        reply_markup=supervisor_selection_keyboard(supervisors),
    )


@router.callback_query(RegistrationFlow.waiting_for_supervisor_selection, F.data.startswith("supervisor:"))
async def on_supervisor_selected(callback: CallbackQuery, state: FSMContext) -> None:
    supervisor_id = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    phone_number = data.get("phone_number")
    telegram_id = callback.message.chat.id if callback.message else callback.from_user.id
    full_name = callback.from_user.full_name if callback.from_user else "User"

    try:
        user = await _register_user({
            "telegram_id": telegram_id,
            "full_name": full_name,
            "phone_number": phone_number,
            "supervisor_id": supervisor_id,
            "role": "user",
        })
        await _finalize_web_login(telegram_id, state)
        await state.clear()
        if callback.message:
            await callback.message.edit_text(
                f"✅ Registration complete! Welcome, {user.get('full_name') or full_name}.",
                reply_markup=None,
            )
            await callback.message.answer("Here is your menu:", reply_markup=main_menu_keyboard())
        await callback.answer()
    except Exception as exc:
        logger.error("User registration failed: %s", exc)
        await callback.answer("Registration failed", show_alert=True)
