"""Pydantic schemas for Medication."""
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class MedicationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    dosage_per_day: int = Field(..., ge=1, le=4)
    timing: Literal["morning", "afternoon", "evening", "custom"] = "custom"
    notes: str | None = Field(None, max_length=500, description="Meal context, e.g. 'after meal'")


class MedicationCreate(MedicationBase):
    user_id: int


class MedicationRead(MedicationBase):
    id: int
    user_id: int

    model_config = {"from_attributes": True}


class MedicationLLM(BaseModel):
    """Schema for what the LLM returns per medication."""
    name: str
    dosage_per_day: int = Field(..., ge=1, le=4)
    timing: Literal["morning", "afternoon", "evening", "custom"] = "custom"
    suggested_times: list[str] = []  # HH:MM strings, length == dosage_per_day
    duration_in_days: int | None = None
    notes: str | None = None
    timing_reasoning: str | None = None

    @field_validator("dosage_per_day", mode="before")
    @classmethod
    def clamp_dosage(cls, v: int) -> int:
        return max(1, min(4, int(v)))


class LLMPrescriptionResponse(BaseModel):
    medications: list[MedicationLLM]
