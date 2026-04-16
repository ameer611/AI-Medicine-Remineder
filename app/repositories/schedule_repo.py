"""Schedule repository."""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleCreate

logger = logging.getLogger(__name__)


class ScheduleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_bulk(self, schedules: list[ScheduleCreate]) -> list[Schedule]:
        objs: list[Schedule] = []
        for s in schedules:
            obj = Schedule(
                medication_id=s.medication_id,
                time=s.time,
                reminder_offset_minutes=s.reminder_offset_minutes,
                duration_in_days=s.duration_in_days,
            )
            self.session.add(obj)
            objs.append(obj)
        await self.session.flush()
        logger.info("Created %d schedule(s)", len(objs))
        return objs

    async def get_by_medication(self, medication_id: int) -> list[Schedule]:
        result = await self.session.execute(
            select(Schedule).where(Schedule.medication_id == medication_id)
        )
        return list(result.scalars().all())
