"""Категории, список и карточка мастер-класса."""

from __future__ import annotations

import html
import logging
from pathlib import Path

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, URLInputFile

from bot.db import open_session
from bot.keyboards import CAT_CODE, masterclass_actions_keyboard, masterclasses_list_keyboard
from config import get_settings
from database import MasterClass
from sqlalchemy import select

router = Router(name="masterclasses")
logger = logging.getLogger(__name__)
# Исправление пути: PROJ_ROOT должен указывать на корень проекта.
# __file__ = bot/handlers/masterclasses.py
# parent = bot/handlers
# parent.parent = bot
# parent.parent.parent = корень проекта
PROJ_ROOT = Path(__file__).resolve().parent.parent.parent


def _decode_cat(code: str) -> str | None:
    """Возвращает название категории по коду или None."""
    return CAT_CODE.get(code)


def _build_photo_input(mc: MasterClass, base_url: str) -> FSInputFile | URLInputFile:
    """
    Локальный файл из data/photos (надёжно для демо) или загрузка по URL.

    Telegram скачивает фото по URL со своих серверов — ngrok/free иногда даёт сбой;
    локальный FSInputFile обходит это.
    """
    raw = (mc.photo_url or "").strip()
    if raw.startswith("/static/photos/"):
        name = raw.rsplit("/", 1)[-1]
        # Исправленный путь: PROJ_ROOT указывает на корень проекта, где лежит папка data
        local = PROJ_ROOT / "data" / "photos" / name
        if local.is_file():
            return FSInputFile(local, filename=name)
    if raw.startswith("http://") or raw.startswith("https://"):
        return URLInputFile(raw)
    return URLInputFile(f"{base_url.rstrip('/')}{raw}")


@router.callback_query(F.data.startswith("cat:"))
async def on_pick_category(callback: CallbackQuery) -> None:
    """Показывает список мастер-классов выбранной категории."""
    code = callback.data.split(":", 1)[1]
    category = _decode_cat(code)
    if not category:
        await callback.answer("Неизвестная категория", show_alert=True)
        return

    async with open_session() as session:
        stmt = (
            select(MasterClass)
            .where(MasterClass.category == category)
            .order_by(MasterClass.date_time)
        )
        rows = (await session.scalars(stmt)).all()

    if not rows:
        await callback.answer("В этой категории пока нет мастер-классов", show_alert=True)
        return

    items = [(r.id, r.name) for r in rows]
    await callback.message.edit_reply_markup(reply_markup=masterclasses_list_keyboard(items, code))
    await callback.answer()


@router.callback_query(F.data.startswith("backcat:"))
async def on_back_to_category_list(callback: CallbackQuery) -> None:
    """Возврат к списку мастер-классов категории."""
    code = callback.data.split(":", 1)[1]
    category = _decode_cat(code)
    if not category:
        await callback.answer("Ошибка категории", show_alert=True)
        return

    async with open_session() as session:
        stmt = (
            select(MasterClass)
            .where(MasterClass.category == category)
            .order_by(MasterClass.date_time)
        )
        rows = (await session.scalars(stmt)).all()
    items = [(r.id, r.name) for r in rows]
    await callback.message.edit_reply_markup(reply_markup=masterclasses_list_keyboard(items, code))
    await callback.answer()


@router.callback_query(F.data.startswith("mc:"))
async def on_masterclass_open(callback: CallbackQuery) -> None:
    """Показывает карточку мастер-класса с фото."""
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Некорректные данные", show_alert=True)
        return
    _, mc_id_s, cat_code = parts
    try:
        mc_id = int(mc_id_s)
    except ValueError:
        await callback.answer("Некорректный id", show_alert=True)
        return
    category = _decode_cat(cat_code)
    if not category:
        await callback.answer("Ошибка категории", show_alert=True)
        return

    async with open_session() as session:
        mc = await session.get(MasterClass, mc_id)
        if mc is None or mc.category != category:
            await callback.answer("Мастер-класс не найден", show_alert=True)
            return

    settings = get_settings()
    base = str(settings.webapp_url)
    photo_input = _build_photo_input(mc, base)

    caption = (
        f"<b>{html.escape(mc.name)}</b>\n"
        f"Категория: {html.escape(mc.category)}\n"
        f"Дата: {mc.date_time.strftime('%d.%m.%Y %H:%M')}\n"
        f"Цена: {mc.price} ₽\n"
        f"Мест: до {mc.max_participants}\n\n"
        f"{html.escape(mc.description or '')}"
    )
    kb = masterclass_actions_keyboard(mc.id, cat_code)
    chat_id = callback.message.chat.id

    try:
        await callback.message.delete()
    except TelegramBadRequest as exc:
        logger.debug("Не удалось удалить сообщение со списком: %s", exc)

    try:
        await callback.bot.send_photo(
            chat_id=chat_id,
            photo=photo_input,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
    except TelegramBadRequest:
        logger.exception("Не удалось отправить фото для МК id=%s, отправляю текст", mc.id)
        try:
            await callback.bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
        except TelegramBadRequest:
            plain = (
                f"{mc.name}\n"
                f"Категория: {mc.category}\n"
                f"Дата: {mc.date_time.strftime('%d.%m.%Y %H:%M')}\n"
                f"Цена: {mc.price} ₽\n"
                f"Мест: до {mc.max_participants}\n\n"
                f"{mc.description or ''}"
            )
            await callback.bot.send_message(chat_id=chat_id, text=plain, reply_markup=kb)

    await callback.answer()
