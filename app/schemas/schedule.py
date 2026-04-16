"""Pydantic schemas for Schedule."""
import re

from pydantic import BaseModel, Field, field_validator


HH_MM_RE = re.compile(r"^\d{2}:\d{2}$")


class ScheduleBase(BaseModel):
    time: str = Field(..., description="HH:MM format")
    reminder_offset_minutes: int = Field(..., ge=0, le=60)
    duration_in_days: int = Field(..., ge=1, le=365)

    @field_validator("time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        if not HH_MM_RE.match(v):
            raise ValueError("time must be in HH:MM format")
        hh, mm = v.split(":")
        if not (0 <= int(hh) <= 23 and 0 <= int(mm) <= 59):
            raise ValueError("Invalid time value")
        return v


class ScheduleCreate(ScheduleBase):
    medication_id: int


class ScheduleRead(ScheduleBase):
    id: int
    medication_id: int

    model_config = {"from_attributes": True}
