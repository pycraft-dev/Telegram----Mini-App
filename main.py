"""Точка входа Telegram-бота (polling)."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.error_handlers import register_global_errors
from bot.handlers import setup_routers
from bot.middlewares import LoggingMiddleware
from config import get_settings
from database import init_db
from utils.logger import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    """Запускает бота и long polling."""
    setup_logging()
    await init_db()
    settings = get_settings()
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(LoggingMiddleware())
    register_global_errors(dp)
    setup_routers(dp)
    logger.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
