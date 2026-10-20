"""Admin handlers for Telegram bot: dashboard, statistics, and callback actions."""

import logging
from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.core.config import settings
from src.core.database import async_session_factory
from src.models import Milestone, MilestoneStatus, Project, ProjectStatus, Ticket, TicketStatus
from src.services.notification_service import notify_client

logger = logging.getLogger(__name__)

router = Router(name="admin_router")


def is_admin_filter(event: types.Message | types.CallbackQuery) -> bool:
    """Filter ensuring user is the configured administrator."""
    if not event.from_user or settings.ADMIN_TELEGRAM_ID is None:
        return False
    return event.from_user.id == settings.ADMIN_TELEGRAM_ID


router.message.filter(is_admin_filter)
router.callback_query.filter(is_admin_filter)


def get_admin_inline_keyboard() -> InlineKeyboardMarkup:
    """Generates admin keyboard with TMA WebAppInfo."""
    web_app_url = settings.WEBAPP_URL.rstrip("/") + "/app"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👨‍💻 Відкрити панель TMA",
                    web_app=WebAppInfo(url=web_app_url),
                )
            ]
        ]
    )


@router.message(CommandStart())
@router.message(Command("admin"))
async def admin_dashboard_handler(message: types.Message) -> None:
    """Displays freelancer/agency dashboard with project statistics."""
    admin_name = settings.ADMIN_USERNAME or "Admin"

    async with async_session_factory() as session:
        # Active projects count
        p_count = await session.scalar(
            select(func.count(Project.id)).where(Project.status == ProjectStatus.ACTIVE)
        )
        # Milestones waiting approval
        m_count = await session.scalar(
            select(func.count(Milestone.id)).where(Milestone.status == MilestoneStatus.WAITING_APPROVAL)
        )
        # Open tickets count
        t_count = await session.scalar(
            select(func.count(Ticket.id)).where(Ticket.status == TicketStatus.OPEN)
        )

    text = (
        f"👨‍💻 <b>Панель керування проектами, @{admin_name}!</b>\n\n"
        f"📊 <b>Зведена статистика:</b>\n"
        f"• Активні проекти: <b>{p_count or 0}</b>\n"
        f"• Етапи на підтвердженні: <b>{m_count or 0}</b>\n"
        f"• Відкриті тікети/правки: <b>{t_count or 0}</b>\n\n"
        f"<i>Використовуйте кнопку нижче для переходу до повного інтерфейсу:</i>"
    )

    await message.answer(
        text,
        reply_markup=get_admin_inline_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("admin_start_milestone:"))
async def callback_admin_start_milestone(call: types.CallbackQuery) -> None:
    """Handles admin clicking button to start working on a milestone."""
    if not call.data:
        return

    milestone_id = int(call.data.split(":")[1])

    async with async_session_factory() as session:
        stmt = (
            select(Milestone)
            .where(Milestone.id == milestone_id)
            .options(selectinload(Milestone.project).selectinload(Project.client))
        )
        milestone = (await session.execute(stmt)).scalar_one_or_none()

        if not milestone:
            await call.answer("Етап не знайдено!", show_alert=True)
            return

        milestone.status = MilestoneStatus.IN_PROGRESS
        await session.commit()
        await session.refresh(milestone)

        client_tg_id = milestone.project.client.telegram_id
        milestone_title = milestone.title

    await call.answer("Статус етапу оновлено на: В роботі!")

    # Update admin notification card message
    if call.message and isinstance(call.message, types.Message):
        updated_text = (
            f"{call.message.html_text}\n\n"
            f"🚀 <b>Роботу над етапом розпочато!</b> (Статус: В роботі)"
        )
        try:
            await call.message.edit_text(updated_text, reply_markup=None, parse_mode="HTML")
        except Exception as exc:
            logger.warning("Could not edit message on milestone start: %s", exc)

    # Notify client
    if call.bot and client_tg_id:
        await notify_client(
            bot=call.bot,
            client_telegram_id=client_tg_id,
            text=f"🚀 <b>Розробник розпочав роботу над етапом «{milestone_title}»!</b>",
        )


@router.callback_query(F.data.startswith("admin_resolve_ticket:"))
async def callback_admin_resolve_ticket(call: types.CallbackQuery) -> None:
    """Handles admin marking ticket as resolved via inline card button."""
    if not call.data:
        return

    ticket_id = int(call.data.split(":")[1])

    async with async_session_factory() as session:
        stmt = (
            select(Ticket)
            .where(Ticket.id == ticket_id)
            .options(selectinload(Ticket.project).selectinload(Project.client))
        )
        ticket = (await session.execute(stmt)).scalar_one_or_none()

        if not ticket:
            await call.answer("Тікет не знайдено!", show_alert=True)
            return

        ticket.status = TicketStatus.RESOLVED
        await session.commit()
        await session.refresh(ticket)

        client_tg_id = ticket.project.client.telegram_id
        ticket_msg = ticket.message

    await call.answer("Тікет вирішено!")

    # Update admin notification message
    if call.message and isinstance(call.message, types.Message):
        updated_text = (
            f"{call.message.html_text}\n\n"
            f"✅ <b>Вирішено розробником.</b>"
        )
        try:
            await call.message.edit_text(updated_text, reply_markup=None, parse_mode="HTML")
        except Exception as exc:
            logger.warning("Could not edit message on ticket resolve: %s", exc)

    # Notify client
    if call.bot and client_tg_id:
        await notify_client(
            bot=call.bot,
            client_telegram_id=client_tg_id,
            text=(
                f"✅ <b>Ваш тікет #{ticket_id} вирішено розробником!</b>\n\n"
                f"<i>«{ticket_msg}»</i>"
            ),
        )
