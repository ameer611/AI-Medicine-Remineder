"""Medication orchestration service."""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.medication_repo import MedicationRepository
from app.repositories.schedule_repo import ScheduleRepository
from app.repositories.user_repo import UserRepository
from app.schemas.medication import MedicationCreate, MedicationRead
from app.schemas.schedule import ScheduleCreate, ScheduleRead

logger = logging.getLogger(__name__)


async def save_medication_with_schedules(
    session: AsyncSession,
    telegram_id: int,
    medication_data: MedicationCreate,
    schedule_times: list[str],
    reminder_offset_minutes: int,
    duration_in_days: int,
) -> tuple[MedicationRead, list[ScheduleRead]]:
    """Persist one medication + its schedules atomically."""
    user_repo = UserRepository(session)
    med_repo = MedicationRepository(session)
    sched_repo = ScheduleRepository(session)

    user, _ = await user_repo.get_or_create(telegram_id)
    medication_data.user_id = user.id

    med = await med_repo.create(medication_data)

    schedule_creates = [
        ScheduleCreate(
            medication_id=med.id,
            time=t,
            reminder_offset_minutes=reminder_offset_minutes,
            duration_in_days=duration_in_days,
        )
        for t in schedule_times
    ]
    schedules = await sched_repo.create_bulk(schedule_creates)
    await session.commit()

    logger.info(
        "Saved medication '%s' with %d schedules for user telegram_id=%s",
        med.name, len(schedules), telegram_id,
    )

    return MedicationRead.model_validate(med), [ScheduleRead.model_validate(s) for s in schedules]


async def get_user_medications(session: AsyncSession, user_id: int) -> list[MedicationRead]:
    med_repo = MedicationRepository(session)
    meds = await med_repo.get_by_user(user_id)
    return [MedicationRead.model_validate(m) for m in meds]


async def get_user_medications_with_schedules(
    session: AsyncSession, user_id: int
) -> list[tuple[MedicationRead, list[ScheduleRead]]]:
    """Return medications and their schedules for a user."""
    med_repo = MedicationRepository(session)
    sched_repo = ScheduleRepository(session)

    meds = await med_repo.get_by_user(user_id)
    result: list[tuple[MedicationRead, list[ScheduleRead]]] = []
    for med in meds:
        schedules = await sched_repo.get_by_medication(med.id)
        result.append(
            (
                MedicationRead.model_validate(med),
                [ScheduleRead.model_validate(s) for s in schedules],
            )
        )
    return result
