"""Маршруты бронирований."""

from __future__ import annotations

import json
import urllib.parse
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.deps import db_session
from api.schemas import BookingCreate, BookingOut, BookingWithClassOut
from config import get_settings
from database import Booking, MasterClass, User
from utils.bot_notifier import notify_booking_created
from utils.notifications import log_reminder_stub
from utils.tg_webapp import WebAppDataInvalidError, extract_telegram_user_id, parse_init_data

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


def _telegram_user_id_skip_validation(init_data: str) -> int:
    """Извлекает user id из init_data без проверки подписи (только для отладки)."""
    pairs = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    user_raw = pairs.get("user")
    if not user_raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="В init_data нет user при SKIP_INIT_DATA_VALIDATION",
        )
    return int(json.loads(user_raw)["id"])


@router.post(
    "",
    response_model=BookingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать бронь",
    responses={
        201: {"description": "Бронь создана"},
        401: {"description": "Неверная подпись initData"},
        409: {"description": "Бронь уже существует"},
    },
)
async def create_booking(
    body: BookingCreate,
    session: Annotated[AsyncSession, Depends(db_session)],
) -> BookingOut:
    """Создаёт бронь после проверки initData и лимитов."""
    settings = get_settings()
    if settings.skip_init_data_validation:
        telegram_user_id = _telegram_user_id_skip_validation(body.init_data)
    else:
        try:
            parsed = parse_init_data(body.init_data, settings.bot_token)
            telegram_user_id = extract_telegram_user_id(parsed)
        except WebAppDataInvalidError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    mc = await session.get(MasterClass, body.master_class_id)
    if mc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Мастер-класс не найден")

    user = await session.scalar(select(User).where(User.telegram_user_id == telegram_user_id))
    if user is None:
        user = User(telegram_user_id=telegram_user_id, username=None, phone=body.phone)
        session.add(user)
        await session.flush()
    else:
        user.phone = body.phone

    booking = Booking(
        user_id=user.id,
        master_class_id=mc.id,
        name=body.name,
        phone=body.phone,
        status="confirmed",
    )
    session.add(booking)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Вы уже записаны на этот мастер-класс",
        ) from exc

    await session.refresh(booking)
    await notify_booking_created(
        telegram_user_id=telegram_user_id,
        master_class_name=mc.name,
        starts_at=mc.date_time,
    )
    log_reminder_stub(booking_id=booking.id, master_class_id=mc.id)
    return BookingOut.model_validate(booking)


@router.get(
    "/{telegram_user_id}",
    response_model=list[BookingWithClassOut],
    summary="Брони пользователя по Telegram ID",
)
async def list_user_bookings(
    telegram_user_id: int,
    session: Annotated[AsyncSession, Depends(db_session)],
) -> list[BookingWithClassOut]:
    """Возвращает брони пользователя (telegram user id)."""
    user = await session.scalar(select(User).where(User.telegram_user_id == telegram_user_id))
    if user is None:
        return []

    stmt = (
        select(Booking)
        .options(selectinload(Booking.master_class))
        .where(Booking.user_id == user.id, Booking.status == "confirmed")
        .order_by(Booking.created_at.desc())
    )
    rows = (await session.scalars(stmt)).all()
    out: list[BookingWithClassOut] = []
    for b in rows:
        mc = b.master_class
        out.append(
            BookingWithClassOut(
                id=b.id,
                user_id=b.user_id,
                master_class_id=b.master_class_id,
                name=b.name,
                phone=b.phone,
                status=b.status,
                created_at=b.created_at,
                master_class_name=mc.name,
                master_class_date_time=mc.date_time,
            )
        )
    return out
