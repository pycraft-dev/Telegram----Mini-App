"""Проверки схемы БД (минимальные)."""

from __future__ import annotations

from database import Base


def test_booking_partial_unique_index_exists() -> None:
    """Таблица bookings содержит частичный уникальный индекс для активных броней."""
    table = Base.metadata.tables.get("bookings")
    assert table is not None
    names = {ix.name for ix in table.indexes}
    assert "uq_booking_user_mc_confirmed" in names
