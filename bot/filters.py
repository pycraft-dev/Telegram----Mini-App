"""Фильтры aiogram."""

from __future__ import annotations

from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from config import get_settings


class AdminFilter(BaseFilter):
    """Пропускает только пользователей из ADMIN_IDS."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        """True, если отправитель в списке администраторов."""
        uid = event.from_user.id if event.from_user else None
        if uid is None:
            return False
        return uid in get_settings().admin_ids
