"""Отправка сообщений через Telegram Bot API (aiogram)."""

from __future__ import annotations

import logging
from datetime import datetime

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import get_settings

logger = logging.getLogger(__name__)


async def send_booking_notification(
    telegram_user_id: int,
    master_class_name: str,
    starts_at: datetime,
) -> None:
    """Отправляет пользователю сообщение об успешной записи."""
    settings = get_settings()
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    when = starts_at.strftime("%d.%m.%Y %H:%M")
    text = (
        f"Вы записаны!\n"
        f"Мастер-класс: <b>{master_class_name}</b>\n"
        f"Дата и время: <b>{when}</b>"
    )
    try:
        await bot.send_message(chat_id=telegram_user_id, text=text)
    except Exception:
        logger.exception("Не удалось отправить уведомление user_id=%s", telegram_user_id)
    finally:
        await bot.session.close()


async def notify_booking_created(
    telegram_user_id: int,
    master_class_name: str,
    starts_at: datetime,
) -> None:
    """Алиас из плана: уведомление пользователя о созданной брони."""
    await send_booking_notification(telegram_user_id, master_class_name, starts_at)
