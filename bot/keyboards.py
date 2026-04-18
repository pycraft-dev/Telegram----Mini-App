"""Inline-клавиатуры бота."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from config import get_settings

CAT_CODE = {
    "kul": "Кулинария",
    "ker": "Керамика",
    "ris": "Рисование",
}


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню после /start."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Расписание", callback_data="menu:schedule")],
            [InlineKeyboardButton(text="📋 Мои записи", callback_data="menu:bookings")],
        ],
    )


def categories_keyboard() -> InlineKeyboardMarkup:
    """Три категории мастер-классов (короткие callback_data)."""
    rows = [
        [InlineKeyboardButton(text="🍳 Кулинария", callback_data="cat:kul")],
        [InlineKeyboardButton(text="🏺 Керамика", callback_data="cat:ker")],
        [InlineKeyboardButton(text="🎨 Рисование", callback_data="cat:ris")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def masterclasses_list_keyboard(items: list[tuple[int, str]], cat_code: str) -> InlineKeyboardMarkup:
    """Список мастер-классов категории."""
    rows: list[list[InlineKeyboardButton]] = []
    for mc_id, title in items:
        rows.append(
            [InlineKeyboardButton(text=title[:64], callback_data=f"mc:{mc_id}:{cat_code}")],
        )
    rows.append([InlineKeyboardButton(text="⬅️ К категориям", callback_data="menu:schedule")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def masterclass_actions_keyboard(master_class_id: int, cat_code: str) -> InlineKeyboardMarkup:
    """WebApp «Записаться» и возврат к списку категории."""
    settings = get_settings()
    base = str(settings.webapp_url).rstrip("/")
    url = f"{base}/?master_class_id={master_class_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ Записаться",
                    web_app=WebAppInfo(url=url),
                )
            ],
            [InlineKeyboardButton(text="⬅️ К списку", callback_data=f"backcat:{cat_code}")],
        ],
    )


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню администратора."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить мастер-класс", callback_data="admin:add")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")],
            [InlineKeyboardButton(text="⬅️ Закрыть", callback_data="admin:close")],
        ],
    )


def bookings_list_keyboard(rows: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    """Список броней с кнопками отмены."""
    buttons: list[list[InlineKeyboardButton]] = []
    for booking_id, label in rows:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"❌ Отменить: {label[:40]}",
                    callback_data=f"bcancel:{booking_id}",
                )
            ],
        )
    buttons.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
