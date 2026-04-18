"""Проверка работоспособности сервиса."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import db_session
from api.schemas import HealthOut

router = APIRouter(prefix="/api", tags=["health"])


@router.get(
    "/health",
    response_model=HealthOut,
    summary="Health check",
    responses={200: {"description": "Сервис и БД доступны"}},
)
async def health(session: AsyncSession = Depends(db_session)) -> HealthOut:
    """Проверяет доступность API и соединения с БД."""
    await session.execute(text("SELECT 1"))
    return HealthOut(status="ok", database="ok")
