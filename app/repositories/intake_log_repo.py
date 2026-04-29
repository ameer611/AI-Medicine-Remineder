"""Repository for IntakeLog operations."""
from datetime import date, datetime

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IntakeLog


class IntakeLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_id: int, medication_id: int, schedule_id: int | None, scheduled_time: str, scheduled_date: date, status: str) -> IntakeLog:
        log = IntakeLog(
            user_id=user_id,
            medication_id=medication_id,
            schedule_id=schedule_id,
            scheduled_time=scheduled_time,
            scheduled_date=scheduled_date,
            status=status,
            logged_at=datetime.utcnow(),
        )
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_by_slot(
        self,
        user_id: int,
        medication_id: int,
        schedule_id: int | None,
        scheduled_time: str,
        scheduled_date: date,
    ) -> IntakeLog | None:
        conditions = [
            IntakeLog.user_id == user_id,
            IntakeLog.medication_id == medication_id,
            IntakeLog.scheduled_time == scheduled_time,
            IntakeLog.scheduled_date == scheduled_date,
        ]
        if schedule_id is None:
            conditions.append(IntakeLog.schedule_id.is_(None))
        else:
            conditions.append(IntakeLog.schedule_id == schedule_id)

        result = await self.session.execute(select(IntakeLog).where(and_(*conditions)).limit(1))
        return result.scalar_one_or_none()

    async def update_status(self, log: IntakeLog, status: str) -> IntakeLog:
        log.status = status
        log.logged_at = datetime.utcnow()
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_by_user_and_date(self, user_id: int, date_: date) -> list[IntakeLog]:
        result = await self.session.execute(
            select(IntakeLog).where(and_(IntakeLog.user_id == user_id, IntakeLog.scheduled_date == date_)).order_by(IntakeLog.scheduled_time)
        )
        return result.scalars().all()

    async def get_by_medication(self, medication_id: int, start_date: date, end_date: date) -> list[IntakeLog]:
        result = await self.session.execute(
            select(IntakeLog).where(
                and_(IntakeLog.medication_id == medication_id, IntakeLog.scheduled_date >= start_date, IntakeLog.scheduled_date <= end_date)
            ).order_by(IntakeLog.scheduled_date, IntakeLog.scheduled_time)
        )
        return result.scalars().all()

    async def count_not_consumed_streak(self, user_id: int, medication_id: int) -> int:
        # Count consecutive most-recent 'not_consumed' entries for this user+medication
        q = (
            select(IntakeLog.status)
            .where(IntakeLog.user_id == user_id, IntakeLog.medication_id == medication_id)
            .order_by(desc(IntakeLog.logged_at))
            .limit(50)
        )
        result = await self.session.execute(q)
        statuses = [row[0] for row in result.fetchall()]
        streak = 0
        for s in statuses:
            if s == "not_consumed":
                streak += 1
            else:
                break
        return streak

    async def get_adherence_stats(self, user_id: int, start_date: date, end_date: date) -> dict:
        total_q = select(func.count()).where(
            and_(IntakeLog.user_id == user_id, IntakeLog.scheduled_date >= start_date, IntakeLog.scheduled_date <= end_date)
        )
        consumed_q = select(func.count()).where(
            and_(IntakeLog.user_id == user_id, IntakeLog.status == "consumed", IntakeLog.scheduled_date >= start_date, IntakeLog.scheduled_date <= end_date)
        )
        not_q = select(func.count()).where(
            and_(IntakeLog.user_id == user_id, IntakeLog.status == "not_consumed", IntakeLog.scheduled_date >= start_date, IntakeLog.scheduled_date <= end_date)
        )
        felt_q = select(func.count()).where(
            and_(IntakeLog.user_id == user_id, IntakeLog.status == "felt_bad", IntakeLog.scheduled_date >= start_date, IntakeLog.scheduled_date <= end_date)
        )
        total = (await self.session.execute(total_q)).scalar_one() or 0
        consumed = (await self.session.execute(consumed_q)).scalar_one() or 0
        not_consumed = (await self.session.execute(not_q)).scalar_one() or 0
        felt_bad = (await self.session.execute(felt_q)).scalar_one() or 0
        adherence_rate = (consumed / total * 100) if total else 0.0
        return {
            "total_scheduled": int(total),
            "consumed": int(consumed),
            "not_consumed": int(not_consumed),
            "felt_bad": int(felt_bad),
            "adherence_rate": float(adherence_rate),
        }

    async def get_supervisor_stats(self, supervisor_id: int, start_date: date, end_date: date) -> list[dict]:
        # Aggregate per user under supervisor
        q = (
            select(IntakeLog.user_id, func.count().label("total"), func.sum(func.if_(IntakeLog.status == "consumed", 1, 0)).label("consumed"))
            .join_from(IntakeLog, IntakeLog.__table__.join)
        )
        # For simplicity, higher-level aggregation will be implemented in service layer
        return []

    async def get_stats_by_medication(self, supervisor_id: int, start_date: date, end_date: date) -> list[dict]:
        # To be implemented in service layer using joins
        return []
