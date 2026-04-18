"""Простой rate limit и вспомогательные middleware."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

_rate_lock = asyncio.Lock()
_rate_buckets: dict[str, list[float]] = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Ограничивает число POST /api/bookings с одного IP."""

    def __init__(self, app: Callable, *, max_requests: int = 30, window_seconds: int = 60) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Пропускает запрос или возвращает 429."""
        path = request.url.path.rstrip("/")
        if request.method == "POST" and path.endswith("/api/bookings"):
            client_ip = request.client.host if request.client else "unknown"
            now = time.monotonic()
            async with _rate_lock:
                bucket = _rate_buckets[client_ip]
                cutoff = now - self.window_seconds
                while bucket and bucket[0] < cutoff:
                    bucket.pop(0)
                if len(bucket) >= self.max_requests:
                    return JSONResponse(
                        {"detail": "Слишком много запросов. Попробуйте позже."},
                        status_code=429,
                    )
                bucket.append(now)
        return await call_next(request)
