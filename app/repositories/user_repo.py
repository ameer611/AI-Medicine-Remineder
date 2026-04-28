"""User repository."""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from datetime import datetime

from app.models.web_session import WebSession

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create(self, telegram_id: int) -> User:
        user = User(telegram_id=telegram_id)
        self.session.add(user)
        await self.session.flush()
        logger.info("Created user telegram_id=%s", telegram_id)
        return user

    async def get_or_create(self, telegram_id: int) -> tuple[User, bool]:
        """Return (user, created). created=True if newly inserted."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            return user, False
        user = await self.create(telegram_id)
        return user, True

    async def get_by_phone(self, phone_number: str) -> User | None:
        result = await self.session.execute(select(User).where(User.phone_number == phone_number))
        return result.scalar_one_or_none()

    async def get_by_web_session_id(self, session_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.web_session_id == session_id))
        return result.scalar_one_or_none()

    async def get_all_supervisors(self) -> list[User]:
        result = await self.session.execute(select(User).where(User.role == "supervisor"))
        return result.scalars().all()

    async def get_users_by_supervisor(self, supervisor_id: int) -> list[User]:
        result = await self.session.execute(select(User).where(User.supervisor_id == supervisor_id))
        return result.scalars().all()

    async def set_web_session(self, telegram_id: int, session_id: str, expires_at: datetime) -> User | None:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            return None
        user.web_session_id = session_id
        user.web_session_expires_at = expires_at
        self.session.add(user)
        await self.session.flush()
        return user

    async def clear_web_session(self, telegram_id: int) -> None:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            return
        user.web_session_id = None
        user.web_session_expires_at = None
        self.session.add(user)
        await self.session.flush()

    async def register_user(
        self, telegram_id: int, full_name: str, phone_number: str, supervisor_id: int | None
    ) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            user = User(telegram_id=telegram_id)
        user.full_name = full_name
        user.phone_number = phone_number
        user.supervisor_id = supervisor_id
        user.role = "user"
        self.session.add(user)
        await self.session.flush()
        return user

    async def register_supervisor(self, telegram_id: int, full_name: str, phone_number: str) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            user = User(telegram_id=telegram_id)
        user.full_name = full_name
        user.phone_number = phone_number
        user.role = "supervisor"
        user.supervisor_id = None
        self.session.add(user)
        await self.session.flush()
        return user
