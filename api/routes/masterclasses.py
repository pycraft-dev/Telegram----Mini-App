"""Маршруты мастер-классов."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import db_session
from api.exceptions import NotFoundError
from api.schemas import MasterClassOut
from database import MasterClass

router = APIRouter(prefix="/api/masterclasses", tags=["masterclasses"])


@router.get(
    "",
    response_model=list[MasterClassOut],
    summary="Список мастер-классов",
)
async def list_masterclasses(
    session: Annotated[AsyncSession, Depends(db_session)],
    category: str | None = Query(default=None, description="Фильтр по категории"),
) -> list[MasterClassOut]:
    """Возвращает список мастер-классов, опционально по категории."""
    stmt = select(MasterClass).order_by(MasterClass.date_time)
    if category:
        stmt = stmt.where(MasterClass.category == category)
    result = await session.scalars(stmt)
    rows = result.all()
    return [MasterClassOut.model_validate(r) for r in rows]


@router.get(
    "/{master_class_id}",
    response_model=MasterClassOut,
    summary="Один мастер-класс",
    responses={404: {"description": "Не найден"}},
)
async def get_masterclass(
    master_class_id: int,
    session: Annotated[AsyncSession, Depends(db_session)],
) -> MasterClassOut:
    """Возвращает карточку мастер-класса по id."""
    obj = await session.get(MasterClass, master_class_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Мастер-класс не найден")
    return MasterClassOut.model_validate(obj)
