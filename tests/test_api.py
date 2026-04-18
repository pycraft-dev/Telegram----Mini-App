"""Базовые тесты HTTP API."""

from __future__ import annotations

import json

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(api_client: AsyncClient) -> None:
    """GET /api/health возвращает ok."""
    r = await api_client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    assert data["service"] == "Melody Mini App"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_api_root_json(api_client: AsyncClient) -> None:
    """GET /api — короткий ответ без БД."""
    r = await api_client.get("/api")
    assert r.status_code == 200
    assert r.json() == {"message": "Melody API is running"}


@pytest.mark.asyncio
async def test_masterclasses_list(api_client: AsyncClient) -> None:
    """После сида список мастер-классов не пустой."""
    r = await api_client.get("/api/masterclasses")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert len(items) >= 3


@pytest.mark.asyncio
async def test_create_booking_and_conflict(api_client: AsyncClient) -> None:
    """Создание брони и конфликт при повторе."""
    r0 = await api_client.get("/api/masterclasses")
    mc_id = r0.json()[0]["id"]

    init_data = "user=" + json.dumps({"id": 999001, "first_name": "Test"})

    body = {
        "init_data": init_data,
        "master_class_id": mc_id,
        "name": "Тест",
        "phone": "+79990000000",
    }
    r1 = await api_client.post("/api/bookings", json=body)
    assert r1.status_code == 201, r1.text

    r2 = await api_client.post("/api/bookings", json=body)
    assert r2.status_code == 409
