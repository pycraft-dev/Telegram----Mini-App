"""Контекстный менеджер сессии БД для хендлеров."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_session_factory


@asynccontextmanager
async def open_session() -> AsyncGenerator[AsyncSession, None]:
    """Открывает async-сессию SQLAlchemy на время операции."""
    settings = get_settings()
    factory = get_session_factory(settings.database_url, echo=settings.sql_echo)
    async with factory() as session:
        yield session
