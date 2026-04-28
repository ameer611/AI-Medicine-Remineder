"""WebSession model for web login ephemeral sessions."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WebSession(Base):
    __tablename__ = "web_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user = relationship("User")

    def __repr__(self) -> str:
        return f"<WebSession id={self.id} session_id={self.session_id} user_id={self.user_id}>"
