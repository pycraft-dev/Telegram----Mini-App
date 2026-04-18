"""Настройка списка команд бота в меню Telegram."""

from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from config import get_settings

logger = logging.getLogger(__name__)


async def setup_bot_commands(bot: Bot) -> None:
    """
    Регистрирует команды в меню (кнопка «Меню» в чате с ботом).

    Для всех пользователей — только /start, если не включён DEMO_MODE.

    Если DEMO_MODE=true — в общем меню добавляется /admin (удобно, когда клиент
    тестирует демо без вашего Telegram ID). Иначе /admin только для ADMIN_IDS.
    """
    settings = get_settings()
    common = [
        BotCommand(command="start", description="Главное меню и расписание"),
    ]
    if settings.demo_mode:
        common.append(BotCommand(command="admin", description="Админ-панель (демо)"))
    await bot.set_my_commands(common, scope=BotCommandScopeDefault())

    admin_menu = [
        BotCommand(command="start", description="Главное меню и расписание"),
        BotCommand(command="admin", description="Админ-панель"),
    ]
    if settings.demo_mode:
        return
    for admin_id in settings.admin_ids:
        try:
            await bot.set_my_commands(
                admin_menu,
                scope=BotCommandScopeChat(chat_id=admin_id),
            )
        except Exception as exc:
            logger.warning(
                "Не удалось установить команды для админа chat_id=%s: %s",
                admin_id,
                exc,
            )
