"""Persistent Reply keyboards for bottom Telegram menu."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from src.core.config import settings


def get_persistent_reply_keyboard() -> ReplyKeyboardMarkup:
    """Returns persistent reply keyboard with TMA launch and main menu buttons."""
    web_app_url = settings.WEBAPP_URL.rstrip("/") + "/app"
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Відкрити кабінет", web_app=WebAppInfo(url=web_app_url)),
                KeyboardButton(text="Головне меню"),
            ]
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
