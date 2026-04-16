"""SQLAlchemy Medication model."""
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage_per_day: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # e.g. "after meal", "before meal"

    user: Mapped["User"] = relationship("User", back_populates="medications")  # type: ignore[name-defined]  # noqa: F821
    schedules: Mapped[list["Schedule"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Schedule", back_populates="medication", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Medication id={self.id} name={self.name} dosage={self.dosage_per_day}>"
