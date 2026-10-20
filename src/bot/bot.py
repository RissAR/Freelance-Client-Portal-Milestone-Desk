"""Telegram Bot configuration and basic handlers using aiogram 3.x."""

import logging
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from src.core.config import settings

logger = logging.getLogger(__name__)

router = Router(name="base_router")


@router.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    """Handles /start command and sends Mini App launch button."""
    web_app_url = settings.WEBAPP_URL.rstrip("/") + "/app"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Open Client Portal",
                    web_app=WebAppInfo(url=web_app_url),
                )
            ]
        ]
    )
    await message.answer(
        f"👋 Вітаємо у <b>Client Portal & Milestone Desk</b>!\n\n"
        f"Тут ви можете переглядати етапи проекту, підписувати акти робіт "
        f"та залишати коментарі.\n\n"
        f"Натисніть кнопку нижче, щоб відкрити портал:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def command_help_handler(message: types.Message) -> None:
    """Handles /help command."""
    await message.answer(
        "ℹ️ <b>Client Portal & Milestone Desk Bot</b>\n\n"
        "Команди:\n"
        "/start - Відкрити головне меню та Mini App\n"
        "/help - Довідка по використанню порталу",
        parse_mode="HTML",
    )


def create_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    """Factory creating configured aiogram Bot and Dispatcher."""
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    return bot, dp
