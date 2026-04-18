"""Фикстуры pytest: окружение и клиент API."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("BOT_TOKEN", "123456:AA-TESTTOKEN")
os.environ.setdefault("SECRET_KEY", "test_secret_key_123456")
os.environ.setdefault("WEBAPP_URL", "https://example.com")
os.environ.setdefault("ADMIN_IDS", "1")
os.environ.setdefault("SKIP_INIT_DATA_VALIDATION", "true")
os.environ.setdefault("LOG_LEVEL", "WARNING")


@pytest_asyncio.fixture
async def api_client(tmp_path_factory: pytest.TempPathFactory) -> AsyncIterator[AsyncClient]:
    """HTTP-клиент поверх ASGI с отдельной файловой БД на тест."""
    from config import clear_settings_cache
    from database import dispose_engine

    db_path = tmp_path_factory.mktemp("db") / "test_api.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path.as_posix()}"
    clear_settings_cache()
    await dispose_engine()

    from api.main import app
    from database import init_db

    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await dispose_engine()
    clear_settings_cache()
