"""Исключения домена API."""


class BookingConflictError(Exception):
    """Пользователь уже имеет активную бронь на этот мастер-класс."""

    def __init__(self, message: str = "Бронь уже существует") -> None:
        super().__init__(message)


class NotFoundError(Exception):
    """Сущность не найдена."""

    pass
