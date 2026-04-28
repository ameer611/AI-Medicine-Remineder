"""Schemas for analytics endpoints."""
from typing import List
from pydantic import BaseModel

from app.schemas.user import UserRead


class AdherenceStats(BaseModel):
    total_scheduled: int
    consumed: int
    not_consumed: int
    felt_bad: int
    adherence_rate: float


class UserAdherenceReport(BaseModel):
    user: UserRead
    stats: AdherenceStats


class MedicationAdherenceReport(BaseModel):
    medication_name: str
    medication_id: int
    stats: AdherenceStats


class SupervisorDashboard(BaseModel):
    total_users: int
    overall_adherence_rate: float
    users: List[UserAdherenceReport]
    by_medication: List[MedicationAdherenceReport]
