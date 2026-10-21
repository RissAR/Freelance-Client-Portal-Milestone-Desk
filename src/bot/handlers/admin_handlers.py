"""Admin handlers for Telegram bot: dashboard, statistics, interactive queues, and callback actions."""

import html
import logging
from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.bot.keyboards.inline import (
    get_admin_back_inline_keyboard,
    get_admin_dashboard_inline_keyboard,
    get_remind_client_inline_keyboard,
)
from src.bot.keyboards.reply import get_persistent_reply_keyboard
from src.core.config import settings
from src.core.database import async_session_factory
from src.models import Milestone, MilestoneStatus, Project, ProjectStatus, Ticket, TicketStatus
from src.services.notification_service import (
    notify_client,
    notify_client_milestone_reminder,
)

logger = logging.getLogger(__name__)

router = Router(name="admin_router")


def is_admin_filter(event: types.Message | types.CallbackQuery) -> bool:
    """Filter ensuring user is the configured administrator."""
    if not event.from_user or settings.ADMIN_TELEGRAM_ID is None:
        return False
    return event.from_user.id == settings.ADMIN_TELEGRAM_ID


router.message.filter(is_admin_filter)
router.callback_query.filter(is_admin_filter)


async def get_dashboard_counts() -> tuple[int, int, int]:
    """Fetches count of active projects, milestones waiting approval, and open tickets."""
    async with async_session_factory() as session:
        p_count = await session.scalar(
            select(func.count(Project.id)).where(Project.status == ProjectStatus.ACTIVE)
        )
        m_count = await session.scalar(
            select(func.count(Milestone.id)).where(Milestone.status == MilestoneStatus.WAITING_APPROVAL)
        )
        t_count = await session.scalar(
            select(func.count(Ticket.id)).where(Ticket.status == TicketStatus.OPEN)
        )
    return p_count or 0, m_count or 0, t_count or 0


def format_dashboard_text(p_count: int, m_count: int, t_count: int) -> str:
    """Formats dashboard message."""
    admin_name = html.escape(settings.ADMIN_USERNAME or "Admin")
    return (
        f"<b>Панель керування проектами, @{admin_name}!</b>\n\n"
        f"<b>Зведена статистика:</b>\n"
        f"• Активні проекти: <b>{p_count}</b>\n"
        f"• Етапи на підтвердженні: <b>{m_count}</b>\n"
        f"• Відкриті тікети/правки: <b>{t_count}</b>\n\n"
        f"<i>Скористайтеся меню для переходу до черг завдань або запуску адмін-кабінету:</i>"
    )


@router.message(CommandStart())
@router.message(Command("admin"))
@router.message(F.text.in_({"📱 Головне меню", "Головне меню", "/menu"}))
async def admin_dashboard_handler(message: types.Message) -> None:
    """Displays freelancer/agency dashboard with live project statistics and persistent reply keyboard."""
    p_count, m_count, t_count = await get_dashboard_counts()

    # Ensure persistent reply keyboard is active
    if message.text and (message.text.startswith("/start") or message.text.startswith("/admin")):
        await message.answer(
            "<b>Client Portal Admin</b> активовано.",
            reply_markup=get_persistent_reply_keyboard(),
            parse_mode="HTML",
        )

    text = format_dashboard_text(p_count, m_count, t_count)
    await message.answer(
        text,
        reply_markup=get_admin_dashboard_inline_keyboard(m_count, t_count),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin_refresh_dashboard")
async def callback_admin_refresh_dashboard(call: types.CallbackQuery) -> None:
    """Refreshes statistics card in place."""
    p_count, m_count, t_count = await get_dashboard_counts()
    text = format_dashboard_text(p_count, m_count, t_count)

    await call.answer("Дані оновлено!", show_alert=False)
    if call.message and isinstance(call.message, types.Message):
        try:
            await call.message.edit_text(
                text,
                reply_markup=get_admin_dashboard_inline_keyboard(m_count, t_count),
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.debug("Dashboard message unchanged: %s", exc)


@router.callback_query(F.data == "admin_waiting_milestones")
async def callback_admin_waiting_milestones(call: types.CallbackQuery) -> None:
    """Displays list of milestones pending client signature with one-click reminder buttons."""
    await call.answer()

    async with async_session_factory() as session:
        stmt = (
            select(Milestone)
            .where(Milestone.status == MilestoneStatus.WAITING_APPROVAL)
            .options(selectinload(Milestone.project).selectinload(Project.client))
            .order_by(Milestone.id.asc())
        )
        milestones = (await session.execute(stmt)).scalars().all()

    if not milestones:
        text = "<b>Наразі немає етапів, що очікують підтвердження.</b>"
        if call.message and isinstance(call.message, types.Message):
            await call.message.answer(text, reply_markup=get_admin_back_inline_keyboard(), parse_mode="HTML")
        return

    if call.message and isinstance(call.message, types.Message):
        await call.message.answer(
            f"<b>Етапи, що очікують підтвердження ({len(milestones)}):</b>",
            parse_mode="HTML",
        )
        for m in milestones:
            p_title = html.escape(m.project.title)
            m_title = html.escape(m.title)
            c_name = html.escape(m.project.client.full_name)
            card = (
                f"<b>{m_title}</b> (#{m.order_index})\n"
                f"Проект: <b>{p_title}</b>\n"
                f"Сума: <b>{m.amount:,.2f} {m.project.currency}</b>\n"
                f"Клієнт: <b>{c_name}</b>"
            )
            await call.message.answer(
                card,
                reply_markup=get_remind_client_inline_keyboard(m.id),
                parse_mode="HTML",
            )


@router.callback_query(F.data.startswith("admin_remind_client:"))
async def callback_admin_remind_client(call: types.CallbackQuery) -> None:
    """Sends a polite review reminder to client for a specific milestone."""
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

    if not milestone or not milestone.project or not milestone.project.client:
        await call.answer("Етап або клієнта не знайдено!", show_alert=True)
        return

    client_tg_id = milestone.project.client.telegram_id
    success = False
    if call.bot and client_tg_id:
        success = await notify_client_milestone_reminder(
            bot=call.bot,
            client_telegram_id=client_tg_id,
            milestone_title=milestone.title,
        )

    if success:
        await call.answer("Нагадування надіслано клієнту!", show_alert=False)
        if call.message and isinstance(call.message, types.Message):
            try:
                await call.message.edit_text(
                    f"{call.message.html_text}\n\n<i>Нагадування надіслано клієнту!</i>",
                    reply_markup=None,
                    parse_mode="HTML",
                )
            except Exception as exc:
                logger.warning("Could not edit reminder card: %s", exc)
    else:
        await call.answer("Не вдалося надіслати сповіщення клієнту.", show_alert=True)


@router.callback_query(F.data == "admin_open_tickets")
async def callback_admin_open_tickets(call: types.CallbackQuery) -> None:
    """Displays open revisions, bugs, and questions with quick resolve actions."""
    await call.answer()

    async with async_session_factory() as session:
        stmt = (
            select(Ticket)
            .where(Ticket.status == TicketStatus.OPEN)
            .options(selectinload(Ticket.project).selectinload(Project.client))
            .order_by(Ticket.id.desc())
        )
        tickets = (await session.execute(stmt)).scalars().all()

    if not tickets:
        text = "<b>Усі тікети вирішено! Відкритих правок немає.</b>"
        if call.message and isinstance(call.message, types.Message):
            await call.message.answer(text, reply_markup=get_admin_back_inline_keyboard(), parse_mode="HTML")
        return

    if call.message and isinstance(call.message, types.Message):
        await call.message.answer(
            f"<b>Відкриті тікети та правки ({len(tickets)}):</b>",
            parse_mode="HTML",
        )
        for t in tickets:
            p_title = html.escape(t.project.title)
            c_name = html.escape(t.project.client.full_name)
            msg_text = html.escape(t.message)
            card = (
                f"<b>Тікет #{t.id} ({t.type.value})</b>\n"
                f"Проект: <b>{p_title}</b>\n"
                f"Клієнт: <b>{c_name}</b>\n"
                f"Текст: <i>{msg_text}</i>"
            )
            keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="Позначити як вирішено",
                            callback_data=f"admin_resolve_ticket:{t.id}",
                        )
                    ]
                ]
            )
            await call.message.answer(card, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "admin_all_projects")
async def callback_admin_all_projects(call: types.CallbackQuery) -> None:
    """Lists all projects with calculated progress and status."""
    await call.answer()

    async with async_session_factory() as session:
        stmt = (
            select(Project)
            .options(
                selectinload(Project.client),
                selectinload(Project.milestones),
            )
            .order_by(Project.created_at.desc())
        )
        projects = (await session.execute(stmt)).scalars().all()

    if not projects:
        text = "Проектів поки не створено."
        if call.message and isinstance(call.message, types.Message):
            await call.message.answer(text, reply_markup=get_admin_back_inline_keyboard(), parse_mode="HTML")
        return

    lines = ["<b>Список проектів:</b>\n"]
    for p in projects:
        total_m = len(p.milestones)
        approved_m = sum(1 for m in p.milestones if m.status == MilestoneStatus.APPROVED)
        progress = round((approved_m / total_m) * 100, 1) if total_m > 0 else 0.0
        p_title = html.escape(p.title)
        c_name = html.escape(p.client.full_name) if p.client else "Не призначено"
        lines.append(
            f"• <b>{p_title}</b>\n"
            f"   Клієнт: {c_name} | Бюджет: {p.budget:,.2f} {p.currency}\n"
            f"   Прогрес: {progress}% ({approved_m}/{total_m} етапів) | Статус: {p.status.value}\n"
        )

    if call.message and isinstance(call.message, types.Message):
        await call.message.answer(
            "\n".join(lines),
            reply_markup=get_admin_back_inline_keyboard(),
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
            f"<b>Роботу над етапом розпочато!</b> (Статус: В роботі)"
        )
        try:
            await call.message.edit_text(updated_text, reply_markup=None, parse_mode="HTML")
        except Exception as exc:
            logger.warning("Could not edit message on milestone start: %s", exc)

    # Notify client
    if call.bot and client_tg_id:
        escaped_title = html.escape(milestone_title)
        await notify_client(
            bot=call.bot,
            client_telegram_id=client_tg_id,
            text=f"<b>Розробник розпочав роботу над етапом «{escaped_title}»!</b>",
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
            f"<b>Вирішено розробником.</b>"
        )
        try:
            await call.message.edit_text(updated_text, reply_markup=None, parse_mode="HTML")
        except Exception as exc:
            logger.warning("Could not edit message on ticket resolve: %s", exc)

    # Notify client
    if call.bot and client_tg_id:
        escaped_msg = html.escape(ticket_msg)
        await notify_client(
            bot=call.bot,
            client_telegram_id=client_tg_id,
            text=(
                f"<b>Ваш тікет #{ticket_id} вирішено розробником!</b>\n\n"
                f"<i>«{escaped_msg}»</i>"
            ),
        )
