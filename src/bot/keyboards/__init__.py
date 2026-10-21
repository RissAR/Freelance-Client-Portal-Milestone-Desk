"""Bot keyboards module package."""

from src.bot.keyboards.inline import (
    get_admin_back_inline_keyboard,
    get_admin_dashboard_inline_keyboard,
    get_client_project_inline_keyboard,
    get_guest_inline_keyboard,
    get_remind_client_inline_keyboard,
)
from src.bot.keyboards.reply import get_persistent_reply_keyboard

__all__ = [
    "get_persistent_reply_keyboard",
    "get_client_project_inline_keyboard",
    "get_guest_inline_keyboard",
    "get_admin_dashboard_inline_keyboard",
    "get_remind_client_inline_keyboard",
    "get_admin_back_inline_keyboard",
]
