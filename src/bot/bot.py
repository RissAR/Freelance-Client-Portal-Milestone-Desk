"""Telegram Bot configuration, handler registration, and bot instance provider."""

import logging
from aiogram import Bot, Dispatcher

from src.bot.handlers.admin_handlers import router as admin_router
from src.bot.handlers.client_handlers import router as client_router
from src.core.config import settings

from aiogram.utils.token import TokenValidationError

logger = logging.getLogger(__name__)

_bot_instance: Bot | None = None


def get_bot() -> Bot | None:
    """Returns the singleton Bot instance for sending notifications."""
    global _bot_instance
    if _bot_instance is None and settings.BOT_TOKEN:
        try:
            _bot_instance = Bot(token=settings.BOT_TOKEN)
        except (TokenValidationError, Exception) as exc:
            logger.warning("Cannot initialize Bot with current BOT_TOKEN: %s", exc)
            return None
    return _bot_instance


def create_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    """Factory creating configured aiogram Bot and Dispatcher with admin and client routers."""
    global _bot_instance

    bot = Bot(token=settings.BOT_TOKEN)
    _bot_instance = bot

    dp = Dispatcher()

    # Register admin router before client router to ensure correct priority
    dp.include_router(admin_router)
    dp.include_router(client_router)

    return bot, dp
