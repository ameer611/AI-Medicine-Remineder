"""Notification service: sends Telegram messages via Bot API."""
from __future__ import annotations

from typing import Optional
import httpx
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.models.medication import Medication

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self) -> None:
        if not settings.BOT_TOKEN:
            logger.warning("BOT_TOKEN not configured; notifications will fail")
        self.bot_token = settings.BOT_TOKEN

    async def _send_telegram_message(self, chat_id: int, text: str) -> None:
        if not self.bot_token:
            logger.error("No BOT_TOKEN configured; cannot send message")
            return
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
            except Exception as exc:
                logger.exception("Failed to send telegram message: %s", exc)

    async def notify_supervisor_felt_bad(self, user_id: int, medication_id: int, db: AsyncSession) -> None:
        user = await db.get(User, user_id)
        med = await db.get(Medication, medication_id)
        if not user or not med:
            logger.warning("notify_supervisor_felt_bad: missing user or medication")
            return
        if not user.supervisor_id:
            logger.info("User %s has no supervisor; skipping notification", user_id)
            return
        supervisor = await db.get(User, user.supervisor_id)
        if not supervisor or not supervisor.telegram_id:
            logger.info("Supervisor missing telegram_id; skipping")
            return
        text = f"⚠️ <b>{user.full_name or 'User'}</b> reported feeling bad after taking <b>{med.name}</b>."
        await self._send_telegram_message(int(supervisor.telegram_id), text)

    async def notify_supervisor_not_consumed_streak(self, user_id: int, medication_id: int, db: AsyncSession) -> None:
        user = await db.get(User, user_id)
        med = await db.get(Medication, medication_id)
        if not user or not med:
            logger.warning("notify_supervisor_not_consumed_streak: missing user or medication")
            return
        if not user.supervisor_id:
            logger.info("User %s has no supervisor; skipping notification", user_id)
            return
        supervisor = await db.get(User, user.supervisor_id)
        if not supervisor or not supervisor.telegram_id:
            logger.info("Supervisor missing telegram_id; skipping")
            return
        text = f"⚠️ <b>{user.full_name or 'User'}</b> has not taken <b>{med.name}</b> 3 times in a row."
        await self._send_telegram_message(int(supervisor.telegram_id), text)
