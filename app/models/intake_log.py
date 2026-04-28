"""IntakeLog model: records user medication intake events."""
from datetime import datetime, date

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class IntakeLog(Base):
    __tablename__ = "intake_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    medication_id: Mapped[int] = mapped_column(Integer, ForeignKey("medications.id", ondelete="CASCADE"), nullable=False)
    schedule_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("schedules.id", ondelete="SET NULL"), nullable=True)
    scheduled_time: Mapped[str] = mapped_column(String(5), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user = relationship("User", back_populates="intake_logs")
    medication = relationship("Medication")
    schedule = relationship("Schedule")

    def __repr__(self) -> str:
        return f"<IntakeLog id={self.id} user_id={self.user_id} med_id={self.medication_id} status={self.status}>"
