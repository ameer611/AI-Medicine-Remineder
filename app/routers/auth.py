"""Authentication routes for web login and bot linking."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import WebSessionCreate, WebSessionStatus
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


@router.post("/session", response_model=WebSessionCreate)
async def create_session(db: AsyncSession = Depends(get_db)):
    return await auth_service.create_web_session(db)


@router.get("/session/{session_id}", response_model=WebSessionStatus)
async def get_session_status(session_id: str, db: AsyncSession = Depends(get_db)):
    try:
        return await auth_service.check_web_session(session_id, db)
    except HTTPException as exc:
        raise exc


@router.post("/bot-link")
async def bot_link(payload: dict, x_internal_key: str | None = Header(None), db: AsyncSession = Depends(get_db)):
    # Internal endpoint called by bot when a user clicks deep-link
    if not settings.INTERNAL_API_KEY or x_internal_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid internal key")
    session_id = payload.get("session_id")
    telegram_id = payload.get("telegram_id")
    if not session_id or not telegram_id:
        raise HTTPException(status_code=400, detail="Missing session_id or telegram_id")
    ok = await auth_service.link_bot_to_session(session_id, int(telegram_id), db)
    return {"success": bool(ok)}


@router.get("/me")
async def me(authorization: str | None = Header(None), db: AsyncSession = Depends(get_db)):
    from app.schemas.user import UserRead

    user = await auth_service.get_current_user(authorization, db)
    return UserRead.model_validate(user)
