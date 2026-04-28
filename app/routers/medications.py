"""POST /medications and GET /medications/{user_id}."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.user_repo import UserRepository
from app.schemas.medication import MedicationCreate, MedicationRead
from app.schemas.schedule import ScheduleRead
from app.services.medication_service import (
    get_user_medications,
    get_user_medications_with_schedules,
    save_medication_with_schedules,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/medications", tags=["Medications"])


class SaveMedicationRequest(BaseModel):
    telegram_id: int
    medication: MedicationCreate
    times: list[str]
    reminder_offset_minutes: int
    duration_in_days: int


class SaveMedicationResponse(BaseModel):
    medication: MedicationRead
    schedules: list[ScheduleRead]


class ActiveMedication(BaseModel):
    medication_id: int
    name: str
    dosage_per_day: int
    times: list[str]
    schedule_ids: list[int] = Field(default_factory=list)
    reminder_offset_minutes: int


class ActiveMedicationsResponse(BaseModel):
    medications: list[ActiveMedication]


@router.post("", response_model=SaveMedicationResponse)
async def save_medication(
    body: SaveMedicationRequest,
    session: AsyncSession = Depends(get_db),
) -> SaveMedicationResponse:
    """Persist a medication with its schedules for a Telegram user."""
    if not body.times:
        raise HTTPException(status_code=400, detail="At least one time is required")
    if len(body.times) != body.medication.dosage_per_day:
        raise HTTPException(
            status_code=400,
            detail=f"Expected {body.medication.dosage_per_day} time(s), got {len(body.times)}",
        )
    if len(set(body.times)) != len(body.times):
        raise HTTPException(status_code=400, detail="Duplicate times are not allowed")

    med, schedules = await save_medication_with_schedules(
        session=session,
        telegram_id=body.telegram_id,
        medication_data=body.medication,
        schedule_times=body.times,
        reminder_offset_minutes=body.reminder_offset_minutes,
        duration_in_days=body.duration_in_days,
    )
    return SaveMedicationResponse(medication=med, schedules=schedules)


@router.get("/{user_id}", response_model=list[MedicationRead])
async def list_medications(
    user_id: int,
    session: AsyncSession = Depends(get_db),
) -> list[MedicationRead]:
    """Return all medications for a given internal user_id."""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await get_user_medications(session, user.id)


@router.get("/{user_id}/active", response_model=ActiveMedicationsResponse)
async def list_active_medications(
    user_id: int,
    session: AsyncSession = Depends(get_db),
) -> ActiveMedicationsResponse:
    """
    Return all medications with at least one schedule for a given Telegram user.

    The `user_id` here corresponds to `telegram_id`.
    """
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    meds = await get_user_medications_with_schedules(session, user.id)

    active: list[ActiveMedication] = []
    for med, schedules in meds:
        if not schedules:
            continue
        ordered = sorted(schedules, key=lambda s: s.time)
        times = [s.time for s in ordered]
        schedule_ids = [s.id for s in ordered]
        # Assume a single offset value per medication; take the first schedule's offset.
        offset = ordered[0].reminder_offset_minutes
        active.append(
            ActiveMedication(
                medication_id=med.id,
                name=med.name,
                dosage_per_day=med.dosage_per_day,
                times=times,
                schedule_ids=schedule_ids,
                reminder_offset_minutes=offset,
            )
        )

    return ActiveMedicationsResponse(medications=active)
