"""Schemas for web authentication and tokens."""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class WebSessionCreate(BaseModel):
    session_id: str
    bot_start_link: str


class WebSessionStatus(BaseModel):
    authenticated: bool
    jwt_token: str | None = None
    user: Optional[dict] = None


class TokenPayload(BaseModel):
    sub: int
    telegram_id: int
    role: str
    exp: int
