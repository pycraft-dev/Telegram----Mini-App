"""Команда /start и навигация по главному меню."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.keyboards import categories_keyboard, main_menu_keyboard

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Приветствие и главное меню."""
    if not message.from_user:
        return
    text = (
        f"Здравствуйте, {message.from_user.full_name}!\n\n"
        "Я помогу записаться на мастер-класс: расписание по категориям, "
        "запись через Mini App и список ваших броней."
    )
    await message.answer(text, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:main")
async def on_menu_main(callback: CallbackQuery) -> None:
    """Возврат в главное меню."""
    await callback.message.edit_reply_markup(reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:schedule")
async def on_menu_schedule(callback: CallbackQuery) -> None:
    """Экран выбора категории."""
    await callback.message.edit_reply_markup(reply_markup=categories_keyboard())
    await callback.answer()
