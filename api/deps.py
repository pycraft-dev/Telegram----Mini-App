"""Зависимости FastAPI."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_session_factory


async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Выдаёт сессию БД на время запроса."""
    settings = get_settings()
    factory = get_session_factory(settings.database_url, echo=settings.sql_echo)
    async with factory() as session:
        yield session
