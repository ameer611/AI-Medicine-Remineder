"""Analytics endpoints for users and supervisors."""
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.user_repo import UserRepository
from app.repositories.intake_log_repo import IntakeLogRepository
from app.repositories.medication_repo import MedicationRepository
from app.services.auth_service import AuthService
from app.schemas.analytics import SupervisorDashboard
from app.schemas.intake_log import IntakeLogRead
from app.schemas.user import UserRead

router = APIRouter(prefix="/analytics", tags=["analytics"])
auth_service = AuthService()


async def _collect_logs_for_user(repo: IntakeLogRepository, user_id: int, start_date, end_date):
    logs = []
    current = start_date
    while current <= end_date:
        logs.extend(await repo.get_by_user_and_date(user_id, current))
        current = current + timedelta(days=1)
    return logs


async def _build_medication_breakdown(db: AsyncSession, logs):
    medication_repo = MedicationRepository(db)
    grouped = defaultdict(list)
    for log in logs:
        grouped[log.medication_id].append(log)

    breakdown = []
    for medication_id, entries in grouped.items():
        medication = await medication_repo.get_by_id(medication_id)
        total = len(entries)
        consumed = sum(1 for entry in entries if entry.status == "consumed")
        not_consumed = sum(1 for entry in entries if entry.status == "not_consumed")
        felt_bad = sum(1 for entry in entries if entry.status == "felt_bad")
        adherence_rate = (consumed / total * 100) if total else 0.0
        breakdown.append(
            {
                "medication_name": medication.name if medication else f"Medication {medication_id}",
                "medication_id": medication_id,
                "stats": {
                    "total_scheduled": total,
                    "consumed": consumed,
                    "not_consumed": not_consumed,
                    "felt_bad": felt_bad,
                    "adherence_rate": adherence_rate,
                },
            }
        )
    return sorted(breakdown, key=lambda item: item["medication_name"])


def _serialize_logs(logs):
    return [IntakeLogRead.model_validate(log).model_dump(mode="json") for log in logs]


@router.get("/user/{telegram_id}")
async def user_analytics(telegram_id: int, start_date: datetime | None = Query(None), end_date: datetime | None = Query(None), db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    repo = IntakeLogRepository(db)
    logs = await _collect_logs_for_user(repo, user.id, start_date.date(), end_date.date())
    stats = await repo.get_adherence_stats(user.id, start_date.date(), end_date.date())
    by_medication = await _build_medication_breakdown(db, logs)
    return {"stats": stats, "logs": _serialize_logs(logs), "by_medication": by_medication}


@router.get("/supervisor/{telegram_id}", response_model=SupervisorDashboard)
async def supervisor_analytics(telegram_id: int, authorization: str | None = Header(None), start_date: datetime | None = Query(None), end_date: datetime | None = Query(None), db: AsyncSession = Depends(get_db)):
    current_user = await auth_service.get_current_user(authorization, db)
    if current_user.role != "supervisor":
        raise HTTPException(status_code=403, detail="Requires supervisor role")
    if current_user.telegram_id != telegram_id:
        raise HTTPException(status_code=403, detail="Can only access your supervisor dashboard")

    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    user_repo = UserRepository(db)
    users = await user_repo.get_users_by_supervisor(current_user.id)
    repo = IntakeLogRepository(db)
    user_reports = []
    total_users = len(users)
    overall_consumed = 0
    overall_total = 0
    overall_not_consumed = 0
    overall_felt_bad = 0
    all_logs = []
    for u in users:
        logs = await _collect_logs_for_user(repo, u.id, start_date.date(), end_date.date())
        stats = await repo.get_adherence_stats(u.id, start_date.date(), end_date.date())
        overall_consumed += stats["consumed"]
        overall_total += stats["total_scheduled"]
        overall_not_consumed += stats["not_consumed"]
        overall_felt_bad += stats["felt_bad"]
        user_reports.append({"user": UserRead.model_validate(u).model_dump(mode="json"), "stats": stats})
        all_logs.extend(logs)

    overall_rate = (overall_consumed / overall_total * 100) if overall_total else 0.0
    stats = {
        "total_scheduled": int(overall_total),
        "consumed": int(overall_consumed),
        "not_consumed": int(overall_not_consumed),
        "felt_bad": int(overall_felt_bad),
        "adherence_rate": float(overall_rate),
    }
    by_medication = await _build_medication_breakdown(db, all_logs)

    dashboard = {
        "total_users": total_users,
        "overall_adherence_rate": overall_rate,
        "stats": stats,
        "users": user_reports,
        "by_medication": by_medication,
        "logs": _serialize_logs(all_logs),
    }
    return dashboard
