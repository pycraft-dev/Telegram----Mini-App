"""Регистрация роутеров хендлеров."""

from aiogram import Dispatcher

from bot.handlers import admin, masterclasses, my_bookings, start


def setup_routers(dp: Dispatcher) -> None:
    """Подключает роутеры к диспетчеру."""
    dp.include_router(admin.router)
    dp.include_router(masterclasses.router)
    dp.include_router(my_bookings.router)
    dp.include_router(start.router)
