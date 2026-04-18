"""Уведомления пользователю и заглушки напоминаний."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def log_reminder_stub(booking_id: int, master_class_id: int) -> None:
    """
    Заглушка напоминания за 24 часа до мастер-класса.

    В демо только пишет в лог.
    """
    logger.info(
        "Напоминание за 24ч (заглушка): booking_id=%s master_class_id=%s",
        booking_id,
        master_class_id,
    )
