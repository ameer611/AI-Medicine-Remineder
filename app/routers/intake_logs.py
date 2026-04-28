"""Endpoints for logging and retrieving intake logs."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.intake_log import IntakeLogCreate, IntakeLogRead
from app.services.intake_log_service import IntakeLogService
from app.repositories.intake_log_repo import IntakeLogRepository
from app.repositories.user_repo import UserRepository

router = APIRouter(prefix="/intake-logs", tags=["intake_logs"])
service = IntakeLogService()


@router.post("", response_model=IntakeLogRead)
async def create_intake(payload: IntakeLogCreate, db: AsyncSession = Depends(get_db)):
    log = await service.log_intake(payload, db)
    return IntakeLogRead.model_validate(log)


@router.get("/user/{telegram_id}", response_model=list[IntakeLogRead])
async def get_user_logs(telegram_id: int, start_date: datetime | None = Query(None), end_date: datetime | None = Query(None), db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
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
        return [IntakeLogRead.model_validate(l) for l in results]
    else:
        # default: return last 7 days
        results = []
        today = datetime.utcnow().date()
        for i in range(7):
            d = today - timedelta(days=i)
            logs = await repo.get_by_user_and_date(user.id, d)
            results.extend(logs)
        return [IntakeLogRead.model_validate(l) for l in results]
