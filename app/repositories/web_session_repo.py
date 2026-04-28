"""Repository for WebSession operations."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.web_session import WebSession


class WebSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, session_id: str, expires_at: datetime) -> WebSession:
        ws = WebSession(session_id=session_id, created_at=datetime.utcnow(), expires_at=expires_at, user_id=None)
        self.session.add(ws)
        await self.session.flush()
        return ws

    async def get_by_session_id(self, session_id: str) -> WebSession | None:
        result = await self.session.execute(select(WebSession).where(WebSession.session_id == session_id))
        return result.scalar_one_or_none()

    async def attach_user(self, session_id: str, user_id: int) -> WebSession | None:
        ws = await self.get_by_session_id(session_id)
        if not ws:
            return None
        ws.user_id = user_id
        self.session.add(ws)
        await self.session.flush()
        return ws

    async def purge_expired(self) -> int:
        # Optional helper to delete expired sessions; implement at service level if needed
        return 0
