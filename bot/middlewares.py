"""Middleware бота."""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Пишет в лог тип апдейта и user id."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Оборачивает хендлер логированием."""
        if isinstance(event, Update):
            uid = None
            if event.message and event.message.from_user:
                uid = event.message.from_user.id
            elif event.callback_query and event.callback_query.from_user:
                uid = event.callback_query.from_user.id
            logger.debug("Update %s user_id=%s", event.event_type, uid)
        return await handler(event, data)
