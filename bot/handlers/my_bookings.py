"""Мои записи и отмена брони."""

from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.db import open_session
from bot.keyboards import bookings_list_keyboard
from database import Booking, User
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = Router(name="my_bookings")


@router.callback_query(F.data == "menu:bookings")
async def on_my_bookings(callback: CallbackQuery) -> None:
    """Показывает подтверждённые брони пользователя."""
    if not callback.from_user or not callback.message:
        await callback.answer()
        return
    tg_id = callback.from_user.id

    async with open_session() as session:
        user = await session.scalar(select(User).where(User.telegram_user_id == tg_id))
        if user is None:
            await callback.answer("У вас пока нет записей", show_alert=True)
            return

        stmt = (
            select(Booking)
            .options(selectinload(Booking.master_class))
            .where(Booking.user_id == user.id, Booking.status == "confirmed")
            .order_by(Booking.created_at.desc())
        )
        rows = (await session.scalars(stmt)).all()
        # Пока сессия открыта — снимаем данные в примитивы (после close ленивые поля падают).
        items: list[tuple[int, str, datetime]] = [
            (b.id, b.master_class.name, b.master_class.date_time) for b in rows
        ]

    if not items:
        await callback.answer("У вас пока нет записей", show_alert=True)
        return

    lines = [
        f"• {name} — {dt.strftime('%d.%m.%Y %H:%M')} (id {bid})" for bid, name, dt in items
    ]
    kb_rows = [(bid, name) for bid, name, _ in items]
    text = "Ваши записи:\n" + "\n".join(lines)
    await callback.message.answer(text, reply_markup=bookings_list_keyboard(kb_rows))
    await callback.answer()


@router.callback_query(F.data.startswith("bcancel:"))
async def on_cancel_booking(callback: CallbackQuery) -> None:
    """Отменяет бронь (статус cancelled)."""
    if not callback.from_user:
        await callback.answer()
        return
    try:
        booking_id = int(callback.data.split(":", 1)[1])
    except (IndexError, ValueError):
        await callback.answer("Некорректный id", show_alert=True)
        return

    tg_id = callback.from_user.id
    async with open_session() as session:
        booking = await session.scalar(
            select(Booking)
            .options(selectinload(Booking.user))
            .where(Booking.id == booking_id),
        )
        if booking is None:
            await callback.answer("Бронь не найдена", show_alert=True)
            return
        if booking.user.telegram_user_id != tg_id:
            await callback.answer("Это не ваша бронь", show_alert=True)
            return
        booking.status = "cancelled"
        await session.commit()

    await callback.answer("Запись отменена")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Бронь отменена. Вы можете записаться снова.")
