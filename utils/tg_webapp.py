"""Проверка подписи данных Telegram WebApp (initData)."""

from __future__ import annotations

import hashlib
import hmac
import json
import urllib.parse
from typing import Any


class WebAppDataInvalidError(ValueError):
    """Подпись initData не совпала или данные повреждены."""


def parse_init_data(init_data: str, bot_token: str) -> dict[str, Any]:
    """
    Проверяет HMAC-подпись initData и возвращает распарсенные поля.

    Алгоритм: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    pairs = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise WebAppDataInvalidError("В initData отсутствует hash")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise WebAppDataInvalidError("Неверная подпись initData")

    result: dict[str, Any] = dict(pairs)
    if "user" in result and isinstance(result["user"], str):
        result["user"] = json.loads(result["user"])
    if "chat_instance" in result:
        try:
            result["chat_instance"] = int(result["chat_instance"])
        except (TypeError, ValueError):
            pass
    if "auth_date" in result:
        try:
            result["auth_date"] = int(result["auth_date"])
        except (TypeError, ValueError):
            pass
    return result


def extract_telegram_user_id(parsed: dict[str, Any]) -> int:
    """Возвращает telegram user id из распарсенного initData."""
    user = parsed.get("user")
    if not isinstance(user, dict) or "id" not in user:
        raise WebAppDataInvalidError("В initData нет user.id")
    return int(user["id"])
