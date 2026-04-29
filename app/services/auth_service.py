"""Authentication & web session service."""
from __future__ import annotations

from datetime import datetime, timedelta
import uuid

import jwt
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import User
from app.repositories.web_session_repo import WebSessionRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import WebSessionCreate, WebSessionStatus, TokenPayload
from app.schemas.user import UserRead


class AuthService:
    def __init__(self) -> None:
        self.jwt_secret = settings.JWT_SECRET
        self.jwt_expire_days = settings.JWT_EXPIRE_DAYS

    async def create_web_session(self, db: AsyncSession) -> WebSessionCreate:
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        repo = WebSessionRepository(db)
        await repo.create(session_id=session_id, expires_at=expires_at)

        if not settings.BOT_USERNAME:
            raise HTTPException(status_code=500, detail="BOT_USERNAME not configured")

        bot_start_link = f"https://t.me/{settings.BOT_USERNAME}?start=web_{session_id}"
        return WebSessionCreate(session_id=session_id, bot_start_link=bot_start_link)

    async def check_web_session(self, session_id: str, db: AsyncSession) -> WebSessionStatus:
        repo = WebSessionRepository(db)
        ws = await repo.get_by_session_id(session_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Session not found")
        if ws.expires_at < datetime.utcnow():
            raise HTTPException(status_code=410, detail="Session expired")

        if not ws.user_id:
            return WebSessionStatus(authenticated=False)

        user = await db.get(User, ws.user_id)
        if not user:
            return WebSessionStatus(authenticated=False)

        token = self.generate_jwt(user)
        user_schema = UserRead.model_validate(user).model_dump()
        return WebSessionStatus(authenticated=True, jwt_token=token, user=user_schema)

    async def link_bot_to_session(self, session_id: str, telegram_id: int, db: AsyncSession) -> bool:
        ws_repo = WebSessionRepository(db)
        ws = await ws_repo.get_by_session_id(session_id)
        if not ws:
            return False

        user_repo = UserRepository(db)
        user, _created = await user_repo.get_or_create(telegram_id)
        await ws_repo.attach_user(session_id=session_id, user_id=user.id)
        await user_repo.set_web_session(telegram_id=telegram_id, session_id=session_id, expires_at=ws.expires_at)
        return True

    def generate_jwt(self, user) -> str:
        if not self.jwt_secret:
            raise HTTPException(status_code=500, detail="JWT_SECRET not configured")
        now = datetime.utcnow()
        exp = now + timedelta(days=int(self.jwt_expire_days))
        payload = {"sub": int(user.id), "telegram_id": int(user.telegram_id), "role": user.role, "exp": int(exp.timestamp())}
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return token

    def verify_jwt(self, token: str) -> TokenPayload:
        if not self.jwt_secret:
            raise HTTPException(status_code=500, detail="JWT_SECRET not configured")
        try:
            decoded = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return TokenPayload.model_validate(decoded)
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")

    def get_token_payload(self, authorization: str | None) -> TokenPayload:
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        try:
            scheme, token = authorization.split()
        except ValueError:
            raise HTTPException(status_code=401, detail="Malformed Authorization header")
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Malformed Authorization header")
        return self.verify_jwt(token)

    async def get_current_user(self, authorization: str | None, db: AsyncSession) -> User:
        payload = self.get_token_payload(authorization)
        user = await db.get(User, int(payload.sub))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
