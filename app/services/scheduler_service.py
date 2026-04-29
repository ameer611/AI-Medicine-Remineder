"""APScheduler service — schedules daily medication reminders."""
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import AsyncSessionFactory
from app.models import Medication

logger = logging.getLogger(__name__)

APP_TIMEZONE = ZoneInfo(settings.TIMEZONE)
scheduler = AsyncIOScheduler(timezone=APP_TIMEZONE)


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started in timezone=%s", settings.TIMEZONE)


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down")


def _make_job_id(prefix: str, chat_id: int, med_name: str, time_str: str, schedule_id: int) -> str:
    safe_name = med_name.replace(" ", "_")
    return f"{prefix}:{chat_id}:{safe_name}:{schedule_id}:{time_str}"


def _build_reply_markup(medication_id: int, schedule_id: int, scheduled_date: str, scheduled_time: str) -> dict:
    def _cb(action: str) -> str:
        return f"intake_{action}:{medication_id}:{schedule_id}:{scheduled_date}:{scheduled_time}"

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Consumed", callback_data=_cb("consumed")),
                InlineKeyboardButton(text="❌ Not consumed", callback_data=_cb("not_consumed")),
                InlineKeyboardButton(text="😟 Feeling bad", callback_data=_cb("felt_bad")),
            ]
        ]
    )
    return markup.model_dump(mode="json")


async def _send_reminder(
    bot_token: str,
    chat_id: int,
    text: str,
    medication_id: int,
    schedule_id: int,
    scheduled_time: str,
) -> None:
    """Fire-and-forget Telegram message from inside a scheduler job."""
    import httpx

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    reply_markup = _build_reply_markup(
        medication_id,
        schedule_id,
        datetime.now(APP_TIMEZONE).date().isoformat(),
        scheduled_time,
    )
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "reply_markup": reply_markup,
                },
            )
        except Exception as exc:
            logger.error("Failed to send reminder to chat_id=%s: %s", chat_id, exc)


def schedule_reminders(
    bot_token: str,
    chat_id: int,
    medication_id: int,
    schedules: list[dict],
    med_name: str,
    notes: str | None,
    offset_minutes: int,
    duration_days: int,
) -> None:
    """For each schedule create before and exact reminder jobs."""
    now = datetime.now(APP_TIMEZONE)
    end_date = now + timedelta(days=duration_days)
    notes_text = f"\n📝 <i>{notes}</i>" if notes else ""

    for schedule in schedules:
        schedule_id = int(schedule["id"])
        time_str = schedule["time"]
        hh, mm = map(int, time_str.split(":"))

        before_dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        before_dt -= timedelta(minutes=offset_minutes)
        before_hh, before_mm = before_dt.hour, before_dt.minute

        before_job_id = _make_job_id("before", chat_id, med_name, time_str, schedule_id)
        before_text = f"💊 <b>Reminder</b>: Time to take {med_name} ({time_str}){notes_text}"

        scheduler.add_job(
            _send_reminder,
            trigger=CronTrigger(hour=before_hh, minute=before_mm, end_date=end_date),
            args=[bot_token, chat_id, before_text, medication_id, schedule_id, time_str],
            id=before_job_id,
            replace_existing=True,
            misfire_grace_time=120,
        )

        exact_job_id = _make_job_id("exact", chat_id, med_name, time_str, schedule_id)
        exact_text = f"💊 <b>Reminder</b>: Time to take {med_name} ({time_str}){notes_text}"

        scheduler.add_job(
            _send_reminder,
            trigger=CronTrigger(hour=hh, minute=mm, end_date=end_date),
            args=[bot_token, chat_id, exact_text, medication_id, schedule_id, time_str],
            id=exact_job_id,
            replace_existing=True,
            misfire_grace_time=120,
        )

        logger.info(
            "Scheduled reminders for '%s' schedule_id=%s at %s (before=%02d:%02d) for %d days",
            med_name, schedule_id, time_str, before_hh, before_mm, duration_days,
        )


async def reload_reminders_from_db() -> None:
    if not settings.BOT_TOKEN:
        logger.warning("BOT_TOKEN missing; cannot restore reminder jobs")
        return

    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(Medication).options(
                selectinload(Medication.user),
                selectinload(Medication.schedules),
            )
        )
        medications = result.scalars().all()

    restored = 0
    for medication in medications:
        if not medication.user or not medication.user.telegram_id or not medication.schedules:
            continue
        schedules = [
            {
                "id": schedule.id,
                "time": schedule.time,
                "reminder_offset_minutes": schedule.reminder_offset_minutes,
                "duration_in_days": schedule.duration_in_days,
            }
            for schedule in medication.schedules
        ]
        duration_days = max(schedule["duration_in_days"] for schedule in schedules)
        offset_minutes = schedules[0]["reminder_offset_minutes"]
        schedule_reminders(
            bot_token=settings.BOT_TOKEN,
            chat_id=int(medication.user.telegram_id),
            medication_id=medication.id,
            schedules=schedules,
            med_name=medication.name,
            notes=medication.notes,
            offset_minutes=offset_minutes,
            duration_days=duration_days,
        )
        restored += len(schedules)

    logger.info("Reloaded %d schedule(s) from the database into APScheduler", restored)
