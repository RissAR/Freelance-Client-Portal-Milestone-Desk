"""Service for sending formatted Telegram notifications to admin and clients."""

import logging
from typing import Any
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.core.config import settings

logger = logging.getLogger(__name__)


async def notify_admin_milestone_approved(
    bot: Bot | None,
    milestone_id: int,
    milestone_title: str,
    amount: float,
    currency: str,
    project_title: str,
    client_name: str,
    next_milestone_id: int | None = None,
) -> bool:
    """Sends notification to agency admin when client approves a milestone."""
    if not bot or not settings.BOT_TOKEN or not settings.ADMIN_TELEGRAM_ID:
        logger.warning(
            "Cannot send admin notification: bot or ADMIN_TELEGRAM_ID is not configured."
        )
        return False

    text = (
        f"🎉 <b>Етап проекту затверджено клієнтом!</b>\n\n"
        f"📁 Проект: <b>{project_title}</b>\n"
        f"📌 Етап: <b>{milestone_title}</b> (id: #{milestone_id})\n"
        f"💰 Сума: <b>{amount:,.2f} {currency}</b>\n"
        f"👤 Клієнт: <b>{client_name}</b>\n"
        f"✍️ <i>Цифровий підпис збережено в системі.</i>\n"
    )

    keyboard = None
    target_milestone_id = next_milestone_id or milestone_id
    if target_milestone_id:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚀 Почати наступний етап",
                        callback_data=f"admin_start_milestone:{target_milestone_id}",
                    )
                ]
            ]
        )

    try:
        await bot.send_message(
            chat_id=settings.ADMIN_TELEGRAM_ID,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        logger.info("Admin notified about approved milestone id=%d", milestone_id)
        return True
    except Exception as exc:
        logger.warning("Failed to notify admin about milestone %d: %s", milestone_id, exc)
        return False


async def notify_admin_ticket_created(
    bot: Bot | None,
    ticket_id: int,
    ticket_type: str,
    message_text: str,
    project_title: str,
    client_name: str,
    attachment_url: str | None = None,
) -> bool:
    """Sends notification card to admin when client submits a new ticket/bug/revision."""
    if not bot or not settings.BOT_TOKEN or not settings.ADMIN_TELEGRAM_ID:
        logger.warning(
            "Cannot send admin notification: bot or ADMIN_TELEGRAM_ID is not configured."
        )
        return False

    type_icon = "🐛" if ticket_type == "BUG" else "✏️" if ticket_type == "REVISION" else "❓"
    text = (
        f"{type_icon} <b>Новий тікет від клієнта #{ticket_id}</b>\n\n"
        f"📁 Проект: <b>{project_title}</b>\n"
        f"👤 Клієнт: <b>{client_name}</b>\n"
        f"🏷 Тип: <b>{ticket_type}</b>\n"
        f"📝 Повідомлення:\n<i>{message_text}</i>\n"
    )
    if attachment_url:
        text += f"\n📎 Вкладення: <a href='{attachment_url}'>Переглянути файл</a>\n"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Позначити як вирішено",
                    callback_data=f"admin_resolve_ticket:{ticket_id}",
                )
            ]
        ]
    )

    try:
        await bot.send_message(
            chat_id=settings.ADMIN_TELEGRAM_ID,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=False,
        )
        logger.info("Admin notified about new ticket id=%d", ticket_id)
        return True
    except Exception as exc:
        logger.warning("Failed to notify admin about ticket %d: %s", ticket_id, exc)
        return False


async def notify_client(
    bot: Bot | None,
    client_telegram_id: int,
    text: str,
    keyboard: InlineKeyboardMarkup | None = None,
) -> bool:
    """Sends notification to client regarding project status update."""
    if not bot or not settings.BOT_TOKEN:
        logger.warning("Cannot notify client: bot is not configured.")
        return False

    try:
        await bot.send_message(
            chat_id=client_telegram_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        logger.info("Client %d notified successfully", client_telegram_id)
        return True
    except Exception as exc:
        logger.warning("Failed to notify client %d: %s", client_telegram_id, exc)
        return False
