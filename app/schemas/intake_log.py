"""Schemas for intake log endpoints."""
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel


class IntakeLogCreate(BaseModel):
    user_id: int
    medication_id: int
    schedule_id: int | None
    scheduled_time: str  # HH:MM
    scheduled_date: date
    status: Literal["consumed", "not_consumed", "felt_bad"]


class IntakeLogRead(BaseModel):
    id: int
    user_id: int
    medication_id: int
    schedule_id: int | None
    scheduled_time: str
    scheduled_date: date
    status: str
    logged_at: datetime

    model_config = {"from_attributes": True}
