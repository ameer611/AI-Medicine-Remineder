"""APScheduler service — schedules daily medication reminders."""
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Module-level singleton scheduler
scheduler = AsyncIOScheduler(timezone="UTC")


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started")


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down")


def _make_job_id(prefix: str, chat_id: int, med_name: str, time_str: str) -> str:
    safe_name = med_name.replace(" ", "_")
    return f"{prefix}:{chat_id}:{safe_name}:{time_str}"


async def _send_reminder(bot_token: str, chat_id: int, text: str) -> None:
    """Fire-and-forget Telegram message from inside a scheduler job."""
    import httpx

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
        except Exception as exc:
            logger.error("Failed to send reminder to chat_id=%s: %s", chat_id, exc)


def schedule_reminders(
    bot_token: str,
    chat_id: int,
    med_name: str,
    notes: str | None,
    times: list[str],
    offset_minutes: int,
    duration_days: int,
) -> None:
    """
    For each time in `times` create two cron jobs:
      1. reminder_before — fires `offset_minutes` before the dose
      2. exact_time      — fires exactly at dose time

    Both jobs auto-expire after `duration_days` days (end_date).
    """
    now = datetime.utcnow()
    end_date = now + timedelta(days=duration_days)
    notes_text = f"\n📝 <i>{notes}</i>" if notes else ""

    for time_str in times:
        hh, mm = map(int, time_str.split(":"))

        # ── Before reminder ────────────────────────────────────────────────
        before_dt = datetime.utcnow().replace(hour=hh, minute=mm, second=0, microsecond=0)
        before_dt -= timedelta(minutes=offset_minutes)
        before_hh, before_mm = before_dt.hour, before_dt.minute

        before_job_id = _make_job_id("before", chat_id, med_name, time_str)
        before_text = (
            f"⏰ <b>Reminder</b>: {med_name} in {offset_minutes} min (at {time_str}){notes_text}"
        )

        scheduler.add_job(
            _send_reminder,
            trigger=CronTrigger(hour=before_hh, minute=before_mm, end_date=end_date),
            args=[bot_token, chat_id, before_text],
            id=before_job_id,
            replace_existing=True,
            misfire_grace_time=120,
        )

        # ── Exact-time reminder ────────────────────────────────────────────
        exact_job_id = _make_job_id("exact", chat_id, med_name, time_str)
        exact_text = f"💊 <b>Time to take</b> {med_name} now!{notes_text}"

        scheduler.add_job(
            _send_reminder,
            trigger=CronTrigger(hour=hh, minute=mm, end_date=end_date),
            args=[bot_token, chat_id, exact_text],
            id=exact_job_id,
            replace_existing=True,
            misfire_grace_time=120,
        )

        logger.info(
            "Scheduled reminders for '%s' at %s (before=%02d:%02d) for %d days",
            med_name, time_str, before_hh, before_mm, duration_days,
        )
