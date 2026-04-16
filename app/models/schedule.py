"""SQLAlchemy Schedule model."""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    medication_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("medications.id", ondelete="CASCADE"), nullable=False
    )
    time: Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM format
    reminder_offset_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    duration_in_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)

    medication: Mapped["Medication"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Medication", back_populates="schedules"
    )

    def __repr__(self) -> str:
        return (
            f"<Schedule id={self.id} time={self.time} "
            f"offset={self.reminder_offset_minutes}min duration={self.duration_in_days}d>"
        )
