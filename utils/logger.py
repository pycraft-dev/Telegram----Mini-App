"""Настройка логирования для бота, API и библиотек."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from config import get_settings


class JsonFormatter(logging.Formatter):
    """Форматер JSON для структурированных логов."""

    def format(self, record: logging.LogRecord) -> str:
        """Собирает JSON-строку из записи лога."""
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> None:
    """Инициализирует корневой логгер и уровни для сторонних библиотек."""
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    if settings.log_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
    root.addHandler(handler)

    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.error").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(level)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO if settings.sql_echo else logging.WARNING)
    logging.getLogger("aiogram").setLevel(level)
