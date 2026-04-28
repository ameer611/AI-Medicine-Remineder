"""User management endpoints (registration, supervisor list)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserRegisterRequest, UserRead, SupervisorRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/supervisors", response_model=list[SupervisorRead])
async def list_supervisors(db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    supervisors = await repo.get_all_supervisors()
    return [SupervisorRead.model_validate(s) for s in supervisors]


@router.get("/{telegram_id}", response_model=UserRead)
async def get_user_by_telegram_id(telegram_id: int, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserRead.model_validate(user)


@router.post("/register", response_model=UserRead)
async def register_user(payload: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    # If supervisor_id provided, validate that it's a supervisor
    if payload.supervisor_id is not None:
        from app.models.user import User as UserModel

        sup = await db.get(UserModel, payload.supervisor_id)
        if not sup or sup.role != "supervisor":
            raise HTTPException(status_code=400, detail="supervisor_id is invalid")

    if payload.role == "supervisor":
        user = await user_repo.register_supervisor(payload.telegram_id, payload.full_name, payload.phone_number)
    else:
        user = await user_repo.register_user(payload.telegram_id, payload.full_name, payload.phone_number, payload.supervisor_id)

    return UserRead.model_validate(user)
