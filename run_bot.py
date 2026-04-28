"""Main runner for the Telegram Bot."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.logging_config import setup_logging
from app.services.scheduler_service import shutdown_scheduler, start_scheduler
from bot.handlers import confirm, edit, image, my_medications, reminder, start, times, registration, web_auth, intake

setup_logging()
logger = logging.getLogger(__name__)


async def main() -> None:
    if not settings.BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Register routers
    dp.include_router(registration.router)
    dp.include_router(web_auth.router)
    dp.include_router(start.router)
    dp.include_router(image.router)
    dp.include_router(confirm.router)
    dp.include_router(edit.router)
    dp.include_router(times.router)
    dp.include_router(reminder.router)
    dp.include_router(my_medications.router)
    dp.include_router(intake.router)

    # Start APScheduler
    start_scheduler()

    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        shutdown_scheduler()


if __name__ == "__main__":
    asyncio.run(main())
