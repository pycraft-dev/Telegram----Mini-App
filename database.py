"""Асинхронное подключение к SQLite и ORM-модели."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text, text, update
from sqlalchemy.event import listen
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс моделей."""

    pass


def _utc_now_naive() -> datetime:
    """Текущее UTC-время без tzinfo (для SQLite datetime)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    """Пользователь Telegram."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class MasterClass(Base):
    """Мастер-класс."""

    __tablename__ = "master_classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    photo_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    date_time: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    max_participants: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="master_class",
        cascade="all, delete-orphan",
    )


class Booking(Base):
    """Бронь на мастер-класс."""

    __tablename__ = "bookings"
    __table_args__ = (
        Index(
            "uq_booking_user_mc_confirmed",
            "user_id",
            "master_class_id",
            unique=True,
            sqlite_where=text("status = 'confirmed'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    master_class_id: Mapped[int] = mapped_column(
        ForeignKey("master_classes.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="confirmed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=_utc_now_naive,
    )

    user: Mapped["User"] = relationship(back_populates="bookings")
    master_class: Mapped["MasterClass"] = relationship(back_populates="bookings")


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _sqlite_connect_pragma(dbapi_conn: object, _record: object) -> None:
    """Включает WAL для SQLite при подключении."""
    cursor = dbapi_conn.cursor()  # type: ignore[union-attr]
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def get_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    """Создаёт или возвращает async-движок."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(database_url, echo=echo, future=True)
        if database_url.startswith("sqlite"):
            listen(_engine.sync_engine, "connect", _sqlite_connect_pragma)
    return _engine


def get_session_factory(database_url: str, *, echo: bool = False) -> async_sessionmaker[AsyncSession]:
    """Фабрика сессий БД."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine(database_url, echo=echo)
        _session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return _session_factory


async def init_models(database_url: str, *, echo: bool = False) -> None:
    """Создаёт таблицы."""
    engine = get_engine(database_url, echo=echo)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Публичные превью (Wikimedia Commons) — реальные фото, без локальных одноцветных заглушек.
DEMO_PHOTO_URLS: dict[str, str] = {
    "pasta": "/static/photos/pasta.png",
    "ceramic": "/static/photos/ceramic.png",
    "watercolor": "/static/photos/watercolor.png",
    "sushi": "/static/photos/sushi.png",
    "pastel": "/static/photos/pastel.png",
}

# Старые пути из первых версий демо → те же URL.
LEGACY_STATIC_PHOTO_MAP: dict[str, str] = {
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/Espaguetis_carbonara.jpg/800px-Espaguetis_carbonara.jpg": DEMO_PHOTO_URLS["pasta"],
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Pottery_wheel.jpg/800px-Pottery_wheel.jpg": DEMO_PHOTO_URLS["ceramic"],
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Watercolor_paints.jpg/800px-Watercolor_paints.jpg": DEMO_PHOTO_URLS["watercolor"],
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Sushi_Rolls_%28124591961%29.jpeg/800px-Sushi_Rolls_%28124591961%29.jpeg": DEMO_PHOTO_URLS["sushi"],
    "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/Oil_pastels.jpg/800px-Oil_pastels.jpg": DEMO_PHOTO_URLS["pastel"],
}


async def seed_demo_data(database_url: str, *, echo: bool = False) -> None:
    """Заполняет демо-данными при пустой таблице master_classes."""
    factory = get_session_factory(database_url, echo=echo)
    async with factory() as session:
        from sqlalchemy import func, select

        count = await session.scalar(select(func.count()).select_from(MasterClass))
        if count and count > 0:
            return

        demos = [
            MasterClass(
                name="Итальянская паста",
                category="Кулинария",
                description="Научимся готовить настоящую пасту карбонара.",
                price=3500,
                photo_url=DEMO_PHOTO_URLS["pasta"],
                date_time=datetime(2026, 6, 15, 18, 0, 0),
                max_participants=10,
            ),
            MasterClass(
                name="Гончарное дело",
                category="Керамика",
                description="Создадим свою первую чашку на гончарном круге.",
                price=2500,
                photo_url=DEMO_PHOTO_URLS["ceramic"],
                date_time=datetime(2026, 6, 17, 14, 0, 0),
                max_participants=6,
            ),
            MasterClass(
                name="Акварель для начинающих",
                category="Рисование",
                description="Основы акварели, пишем пейзаж.",
                price=2000,
                photo_url=DEMO_PHOTO_URLS["watercolor"],
                date_time=datetime(2026, 6, 20, 11, 0, 0),
                max_participants=8,
            ),
            MasterClass(
                name="Суши и роллы",
                category="Кулинария",
                description="Домашние роллы: рис, нори, начинки.",
                price=4200,
                photo_url=DEMO_PHOTO_URLS["sushi"],
                date_time=datetime(2026, 7, 5, 17, 0, 0),
                max_participants=8,
            ),
            MasterClass(
                name="Масло и пастель",
                category="Рисование",
                description="Портрет в смешанной технике.",
                price=2800,
                photo_url=DEMO_PHOTO_URLS["pastel"],
                date_time=datetime(2026, 7, 12, 15, 0, 0),
                max_participants=10,
            ),
        ]
        session.add_all(demos)
        await session.commit()


async def migrate_legacy_photo_urls(database_url: str, *, echo: bool = False) -> None:
    """Подменяет старые /static/photos/*.png на реальные URL в уже существующей БД."""
    factory = get_session_factory(database_url, echo=echo)
    async with factory() as session:
        for old, new in LEGACY_STATIC_PHOTO_MAP.items():
            await session.execute(update(MasterClass).where(MasterClass.photo_url == old).values(photo_url=new))
        await session.commit()


def _solid_rgb_png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    """
    Собирает несжатый по строкам RGB8 PNG (без внешних зависимостей).

    Раньше использовалась 1×1 прозрачная заглушка — в Telegram и Mini App
    при object-fit:cover это выглядело как пустое/белое поле.
    """
    import struct
    import zlib

    def _chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    r, g, b = rgb
    rows: list[bytes] = []
    px = bytes([r, g, b])
    for _ in range(height):
        rows.append(bytes([0]) + px * width)
    raw = b"".join(rows)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(raw, 9))
        + _chunk(b"IEND", b"")
    )


def ensure_photo_placeholders() -> None:
    """Создаёт демо-PNG в data/photos (цветные превью, если файла нет или это старая 1×1 заглушка)."""
    root = Path(__file__).resolve().parent
    photos = root / "data" / "photos"
    photos.mkdir(parents=True, exist_ok=True)
    # Теперь мы используем сгенерированные нейросетью картинки,
    # поэтому этот метод просто проверяет, что директория существует.
    # Если файлов нет, они будут отдавать 404, но бот не упадёт.


async def init_db(database_url: str | None = None, *, echo: bool | None = None) -> None:
    """Инициализация БД: таблицы, фото-заглушки, сид."""
    from config import get_settings

    settings = get_settings()
    url = database_url or settings.database_url
    sql_echo = settings.sql_echo if echo is None else echo
    ensure_photo_placeholders()
    await init_models(url, echo=sql_echo)
    await seed_demo_data(url, echo=sql_echo)
    await migrate_legacy_photo_urls(url, echo=sql_echo)


async def dispose_engine() -> None:
    """Освобождает пул соединений (для тестов)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
