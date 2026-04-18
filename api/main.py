"""Точка входа FastAPI: API, статика Mini App, middleware."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routes import bookings, health, masterclasses
from config import get_settings
from database import init_db
from api.middleware import RateLimitMiddleware
from utils.logger import setup_logging

logger = logging.getLogger(__name__)
_ROOT = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при старте и освобождение ресурсов."""
    setup_logging()
    await init_db()
    logger.info("API готов, БД инициализирована")
    yield


def _cors_origins() -> list[str]:
    """Собирает список разрешённых CORS origins."""
    settings = get_settings()
    origins: list[str] = [str(settings.webapp_url).rstrip("/")]
    if settings.cors_origins:
        for o in settings.cors_origins:
            if o not in origins:
                origins.append(o.rstrip("/"))
    return origins


def create_app() -> FastAPI:
    """Создаёт и настраивает приложение FastAPI."""
    app = FastAPI(
        title="Демо: запись на мастер-классы",
        description="REST API и раздача Mini App для Telegram WebApp",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Возвращает детали ошибок валидации."""
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        """Логирует непойманные исключения и отвечает 500."""
        logger.exception("Необработанная ошибка: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Внутренняя ошибка сервера"})

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware, max_requests=40, window_seconds=60)

    app.include_router(health.router)
    app.include_router(masterclasses.router)
    app.include_router(bookings.router)

    photos_dir = _ROOT / "data" / "photos"
    photos_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static/photos", StaticFiles(directory=str(photos_dir)), name="photos")

    mini_dir = _ROOT / "mini_app"
    app.mount("/", StaticFiles(directory=str(mini_dir), html=True), name="mini_app")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
