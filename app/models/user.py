"""SQLAlchemy User model."""
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)

    # Registration fields (filled after /register flow)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True, index=True)

    # Role: regular user or supervisor
    role: Mapped[str] = mapped_column(
        Enum("user", "supervisor", name="user_role"),
        nullable=False,
        default="user",
        server_default="user",
    )

    # Self-referential: which supervisor manages this user
    supervisor_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Ephemeral web-login session fields (mirrored from WebSession for quick lookup)
    web_session_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    web_session_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    medications: Mapped[list["Medication"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Medication", back_populates="user", cascade="all, delete-orphan"
    )
    intake_logs: Mapped[list["IntakeLog"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "IntakeLog", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} telegram_id={self.telegram_id} role={self.role}>"
