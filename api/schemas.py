"""Pydantic-схемы запросов и ответов API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MasterClassOut(BaseModel):
    """Мастер-класс в ответе API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    description: str
    price: int
    photo_url: str
    date_time: datetime
    max_participants: int


class BookingCreate(BaseModel):
    """Тело запроса на создание брони из Mini App."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "init_data": "query_id=...&user=%7B%22id%22%3A123%7D&auth_date=...&hash=...",
                    "master_class_id": 1,
                    "name": "Иван",
                    "phone": "+79990001122",
                }
            ]
        }
    )

    init_data: str = Field(..., description="Сырой initData из Telegram.WebApp")
    master_class_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=5, max_length=64)


class BookingOut(BaseModel):
    """Созданная бронь."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    master_class_id: int
    name: str
    phone: str
    status: str
    created_at: datetime


class BookingWithClassOut(BookingOut):
    """Бронь с краткой информацией о мастер-классе."""

    master_class_name: str
    master_class_date_time: datetime
