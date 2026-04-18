"""Админ-панель: добавление мастер-класса и статистика."""

from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.db import open_session
from bot.filters import AdminFilter
from bot.keyboards import admin_menu_keyboard
from config import get_settings
from database import Booking, MasterClass, User
from sqlalchemy import func, select

router = Router(name="admin")


class AddMasterClassForm(StatesGroup):
    """Шаги добавления мастер-класса."""

    name = State()
    category = State()
    description = State()
    price = State()
    date_time = State()
    max_participants = State()
    photo_url = State()


def _is_admin(user_id: int | None) -> bool:
    """Проверяет, входит ли пользователь в ADMIN_IDS (или включён демо-режим)."""
    if user_id is None:
        return False
    settings = get_settings()
    if settings.demo_mode:
        return True
    return user_id in settings.admin_ids


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    """Открывает админ-меню."""
    if not message.from_user or not _is_admin(message.from_user.id):
        await message.answer("Команда доступна только администраторам.")
        return
    await state.clear()
    await message.answer("Админ-панель", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "admin:close", AdminFilter())
async def admin_close(callback: CallbackQuery, state: FSMContext) -> None:
    """Закрывает админ-меню."""
    await state.clear()
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "admin:stats", AdminFilter())
async def admin_stats(callback: CallbackQuery) -> None:
    """Краткая статистика по броням и мастер-классам."""
    async with open_session() as session:
        mc_count = await session.scalar(select(func.count()).select_from(MasterClass))
        b_conf = await session.scalar(
            select(func.count()).select_from(Booking).where(Booking.status == "confirmed"),
        )
        users_count = await session.scalar(select(func.count()).select_from(User))

    text = (
        "Статистика:\n"
        f"Мастер-классов: {mc_count}\n"
        f"Активных броней: {b_conf}\n"
        f"Пользователей в базе: {users_count}"
    )
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == "admin:add", AdminFilter())
async def admin_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начинает сценарий добавления мастер-класса."""
    await state.set_state(AddMasterClassForm.name)
    await callback.message.answer("Введите название мастер-класса:")
    await callback.answer()


@router.message(AddMasterClassForm.name, AdminFilter())
async def admin_add_name(message: Message, state: FSMContext) -> None:
    """Сохраняет название."""
    await state.update_data(name=message.text.strip())
    await state.set_state(AddMasterClassForm.category)
    await message.answer("Введите категорию: Кулинария, Керамика или Рисование")


@router.message(AddMasterClassForm.category, AdminFilter())
async def admin_add_category(message: Message, state: FSMContext) -> None:
    """Сохраняет категорию."""
    cat = message.text.strip()
    allowed = {"Кулинария", "Керамика", "Рисование"}
    if cat not in allowed:
        await message.answer("Укажите одну из категорий: Кулинария, Керамика, Рисование")
        return
    await state.update_data(category=cat)
    await state.set_state(AddMasterClassForm.description)
    await message.answer("Введите описание (кратко):")


@router.message(AddMasterClassForm.description, AdminFilter())
async def admin_add_description(message: Message, state: FSMContext) -> None:
    """Сохраняет описание."""
    await state.update_data(description=message.text.strip())
    await state.set_state(AddMasterClassForm.price)
    await message.answer("Введите цену (целое число, руб.):")


@router.message(AddMasterClassForm.price, AdminFilter())
async def admin_add_price(message: Message, state: FSMContext) -> None:
    """Сохраняет цену."""
    try:
        price = int(message.text.strip())
    except ValueError:
        await message.answer("Нужно целое число. Повторите ввод цены:")
        return
    await state.update_data(price=price)
    await state.set_state(AddMasterClassForm.date_time)
    await message.answer("Введите дату и время в формате ГГГГ-ММ-ДД ЧЧ:ММ (например 2026-08-01 16:00)")


@router.message(AddMasterClassForm.date_time, AdminFilter())
async def admin_add_dt(message: Message, state: FSMContext) -> None:
    """Сохраняет дату и время."""
    raw = message.text.strip()
    try:
        dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
    except ValueError:
        await message.answer("Неверный формат. Пример: 2026-08-01 16:00")
        return
    await state.update_data(date_time=dt)
    await state.set_state(AddMasterClassForm.max_participants)
    await message.answer("Введите максимум участников (целое число):")


@router.message(AddMasterClassForm.max_participants, AdminFilter())
async def admin_add_max(message: Message, state: FSMContext) -> None:
    """Сохраняет лимит участников."""
    try:
        mx = int(message.text.strip())
    except ValueError:
        await message.answer("Нужно целое число участников:")
        return
    await state.update_data(max_participants=mx)
    await state.set_state(AddMasterClassForm.photo_url)
    await message.answer("Введите URL фото (https://...) или путь /static/photos/....png")


@router.message(AddMasterClassForm.photo_url, AdminFilter())
async def admin_add_photo(message: Message, state: FSMContext) -> None:
    """Сохраняет URL фото и создаёт запись."""
    url = message.text.strip()
    data = await state.get_data()
    await state.clear()

    mc = MasterClass(
        name=data["name"],
        category=data["category"],
        description=data["description"],
        price=int(data["price"]),
        photo_url=url,
        date_time=data["date_time"],
        max_participants=int(data["max_participants"]),
    )
    async with open_session() as session:
        session.add(mc)
        await session.commit()

    await message.answer("Мастер-класс добавлен и доступен в расписании.")
