"""Глобальная обработка ошибок в хендлерах бота."""

from __future__ import annotations

import logging

from aiogram import Dispatcher
from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)


async def global_error_handler(event: ErrorEvent) -> bool:
    """
    Логирует исключение и отправляет пользователю краткое уведомление.

    Возвращает True, чтобы пометить ошибку как обработанную.
    """
    logger.exception("Ошибка при обработке апдейта: %s", event.exception)
    try:
        upd = event.update
        if upd.callback_query:
            await upd.callback_query.answer("Произошла ошибка.", show_alert=True)
        elif upd.message:
            await upd.message.answer("Произошла ошибка. Попробуйте позже.")
    except Exception:
        logger.exception("Не удалось отправить сообщение об ошибке пользователю")
    return True


def register_global_errors(dp: Dispatcher) -> None:
    """Регистрирует обработчик ошибок на диспетчере."""
    dp.errors.register(global_error_handler)
