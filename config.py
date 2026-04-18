"""Загрузка настроек приложения из переменных окружения и .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, HttpUrl, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень проекта (рядом с config.py лежит .env)
_ROOT = Path(__file__).resolve().parent
_ENV_FILE = _ROOT / ".env"


class Settings(BaseSettings):
    """Конфигурация бота и API."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(..., description="Токен Telegram-бота")
    database_url: str = Field(
        default="sqlite+aiosqlite:///./demo.db",
        description="Строка подключения SQLAlchemy async",
    )
    secret_key: str = Field(..., min_length=8, description="Секрет для демо-заголовков/тестов")
    admin_ids: list[int] = Field(default_factory=list, description="Telegram ID администраторов")
    demo_mode: bool = Field(
        default=False,
        description="Демо для клиента: /admin и админ-кнопки доступны всем (только тестовый стенд!)",
    )
    webapp_url: HttpUrl = Field(..., description="Публичный HTTPS URL Mini App (ngrok)")

    skip_init_data_validation: bool = Field(
        default=False,
        description="Пропуск проверки подписи initData (только отладка)",
    )
    cors_origins: list[str] | None = Field(
        default=None,
        description="Дополнительные CORS origins; если None — только WEBAPP_URL",
    )

    log_level: str = Field(default="INFO", description="Уровень логирования")
    sql_echo: bool = Field(default=False, description="Логировать SQL в консоль")
    log_json: bool = Field(default=False, description="JSON-формат логов")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str] | None:
        """Парсит CORS_ORIGINS из строки с запятыми."""
        if value is None or value == "":
            return None
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        if isinstance(value, str):
            parts = [p.strip() for p in value.split(",") if p.strip()]
            return parts or None
        raise TypeError("cors_origins должен быть списком или строкой")

    @field_validator("demo_mode", mode="before")
    @classmethod
    def parse_demo_mode(cls, value: Any) -> bool:
        """Парсит DEMO_MODE из строки окружения."""
        if value is None or value == "":
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return bool(value)

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: Any) -> list[int]:
        """Парсит ADMIN_IDS из строки с запятыми или списка."""
        if value is None or value == "":
            return []
        if isinstance(value, int):
            return [value]
        if isinstance(value, list):
            return [int(x) for x in value]
        if isinstance(value, str):
            parts = [p.strip() for p in value.split(",") if p.strip()]
            return [int(p) for p in parts]
        raise TypeError("admin_ids должен быть списком или строкой с числами через запятую")

    @field_validator("database_url")
    @classmethod
    def database_url_sqlite_only(cls, value: str) -> str:
        """
        Проверяет строку БД для демо.

        Частая ошибка: вставить URL ngrok (https://...) в DATABASE_URL — SQLAlchemy
        тогда пытается загрузить несуществующий диалект «https».
        """
        v = (value or "").strip()
        low = v.lower()
        if low.startswith("http://") or low.startswith("https://"):
            raise ValueError(
                "DATABASE_URL не должен быть http(s)-адресом. "
                "Адрес ngrok указывается только в WEBAPP_URL. "
                "Для SQLite используйте: sqlite+aiosqlite:///./demo.db"
            )
        if not low.startswith("sqlite"):
            raise ValueError(
                "В этом демо DATABASE_URL должен начинаться с sqlite "
                "(например sqlite+aiosqlite:///./demo.db)."
            )
        return v


@lru_cache
def get_settings() -> Settings:
    """Возвращает закэшированный экземпляр настроек."""
    try:
        return Settings()
    except ValidationError as exc:
        raise RuntimeError(
            "Не заданы обязательные переменные. Скопируйте .env.example в файл .env в корне проекта "
            "и заполните как минимум: BOT_TOKEN, SECRET_KEY, WEBAPP_URL."
        ) from exc


def clear_settings_cache() -> None:
    """Сбрасывает кэш настроек (для тестов)."""
    get_settings.cache_clear()
