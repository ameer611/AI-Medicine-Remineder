"""Endpoints for logging and retrieving intake logs."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.intake_log import IntakeLogCreate, IntakeLogRead
from app.services.intake_log_service import IntakeLogService
from app.repositories.intake_log_repo import IntakeLogRepository
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(prefix="/intake-logs", tags=["intake_logs"])
service = IntakeLogService()
auth_service = AuthService()


def _to_read_model(log) -> IntakeLogRead:
    return IntakeLogRead(
        id=log.id,
        user_id=log.user_id,
        medication_id=log.medication_id,
        schedule_id=log.schedule_id,
        scheduled_time=log.scheduled_time,
        scheduled_date=log.scheduled_date,
        status=log.status,
        logged_at=log.logged_at,
    )


@router.post("", response_model=IntakeLogRead)
async def create_intake(payload: IntakeLogCreate, authorization: str | None = Header(None), db: AsyncSession = Depends(get_db)):
    current_user = await auth_service.get_current_user(authorization, db)
    if current_user.id != payload.user_id:
        raise HTTPException(status_code=403, detail="Cannot create intake logs for another user")
    log = await service.log_intake(payload, db)
    return _to_read_model(log)


@router.get("/user/{telegram_id}", response_model=list[IntakeLogRead])
async def get_user_logs(telegram_id: int, authorization: str | None = Header(None), start_date: datetime | None = Query(None), end_date: datetime | None = Query(None), db: AsyncSession = Depends(get_db)):
    current_user = await auth_service.get_current_user(authorization, db)
    user_repo = UserRepository(db)
    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    is_self = current_user.telegram_id == telegram_id
    is_supervisor_of_user = current_user.role == "supervisor" and user.supervisor_id == current_user.id
    if not is_self and not is_supervisor_of_user:
        raise HTTPException(status_code=403, detail="Cannot access intake logs for this user")
    repo = IntakeLogRepository(db)
    # If dates provided, fetch per-day; current repo supports exact date queries via get_by_user_and_date
    if start_date and end_date:
        # naive: collect logs between dates
        results = []
        cur = start_date
        while cur.date() <= end_date.date():
            logs = await repo.get_by_user_and_date(user.id, cur.date())
            results.extend(logs)
            cur = cur + timedelta(days=1)
        return [_to_read_model(log) for log in results]
    else:
        # default: return last 7 days
        results = []
        today = datetime.utcnow().date()
        for i in range(7):
            d = today - timedelta(days=i)
            logs = await repo.get_by_user_and_date(user.id, d)
            results.extend(logs)
        return [_to_read_model(log) for log in results]
