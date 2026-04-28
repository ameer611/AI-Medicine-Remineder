"""Service to handle intake log creation and related business logic."""
from __future__ import annotations

from datetime import date
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.intake_log_repo import IntakeLogRepository
from app.repositories.user_repo import UserRepository
from app.services.notification_service import NotificationService
from app.schemas.intake_log import IntakeLogCreate

logger = logging.getLogger(__name__)


class IntakeLogService:
    def __init__(self, notification_service: NotificationService | None = None) -> None:
        self.notification_service = notification_service or NotificationService()

    async def log_intake(self, data: IntakeLogCreate, db: AsyncSession):
        intake_repo = IntakeLogRepository(db)
        log = await intake_repo.create(
            user_id=data.user_id,
            medication_id=data.medication_id,
            schedule_id=data.schedule_id,
            scheduled_time=data.scheduled_time,
            scheduled_date=data.scheduled_date,
            status=data.status,
        )

        # If felt bad -> notify supervisor
        if data.status == "felt_bad":
            await self.notification_service.notify_supervisor_felt_bad(data.user_id, data.medication_id, db)

        # If not_consumed -> check streak
        if data.status == "not_consumed":
            streak = await intake_repo.count_not_consumed_streak(data.user_id, data.medication_id)
            logger.info("User %s medication %s not_consumed streak=%s", data.user_id, data.medication_id, streak)
            if streak >= 3:
                await self.notification_service.notify_supervisor_not_consumed_streak(data.user_id, data.medication_id, db)

        return log
