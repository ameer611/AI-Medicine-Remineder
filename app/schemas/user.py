"""Pydantic schemas for user endpoints."""
from typing import Literal
from pydantic import BaseModel


class UserRegisterRequest(BaseModel):
    telegram_id: int
    full_name: str
    phone_number: str
    supervisor_id: int | None = None
    role: Literal["user", "supervisor"] = "user"


class UserRead(BaseModel):
    id: int
    telegram_id: int
    full_name: str | None
    phone_number: str | None
    role: str
    supervisor_id: int | None

    model_config = {"from_attributes": True}


class SupervisorRead(BaseModel):
    id: int
    telegram_id: int
    full_name: str | None

    model_config = {"from_attributes": True}
