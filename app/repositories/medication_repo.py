"""Medication repository."""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Medication
from app.schemas.medication import MedicationCreate

logger = logging.getLogger(__name__)


class MedicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: MedicationCreate) -> Medication:
        med = Medication(
            user_id=data.user_id,
            name=data.name,
            dosage_per_day=data.dosage_per_day,
            notes=data.notes,
        )
        self.session.add(med)
        await self.session.flush()
        logger.info("Created medication id=%s name=%s", med.id, med.name)
        return med

    async def get_by_user(self, user_id: int) -> list[Medication]:
        result = await self.session.execute(
            select(Medication)
            .where(Medication.user_id == user_id)
            .options(selectinload(Medication.schedules))
        )
        return list(result.scalars().all())

    async def get_by_id(self, medication_id: int) -> Medication | None:
        result = await self.session.execute(
            select(Medication)
            .where(Medication.id == medication_id)
            .options(selectinload(Medication.schedules))
        )
        return result.scalar_one_or_none()
