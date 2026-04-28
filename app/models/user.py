"""SQLAlchemy User model."""
from datetime import datetime
from typing import List

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, index=True)
    role: Mapped[str] = mapped_column(Enum("user", "supervisor", name="user_role"), nullable=False, default="user")
    supervisor_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    web_session_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    web_session_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    medications: Mapped[list["Medication"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Medication", back_populates="user", cascade="all, delete-orphan"
    )

    supervisor: Mapped["User" | None] = relationship("User", remote_side="User.id", foreign_keys=[supervisor_id])
    supervised_users: Mapped[list["User"]] = relationship("User", foreign_keys="User.supervisor_id")
    intake_logs: Mapped[list["IntakeLog"]] = relationship("IntakeLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} telegram_id={self.telegram_id} full_name={self.full_name}>"
