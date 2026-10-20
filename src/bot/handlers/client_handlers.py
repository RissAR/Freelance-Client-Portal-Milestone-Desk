"""Client handlers for Telegram bot: project dashboard, status, and TMA portal link."""

import logging
from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.config import settings
from src.core.database import async_session_factory
from src.models import Milestone, MilestoneStatus, Project, ProjectStatus, User

logger = logging.getLogger(__name__)

router = Router(name="client_router")


def is_client_filter(message: types.Message) -> bool:
    """Filter ensuring user is not the configured administrator."""
    if not message.from_user:
        return False
    if settings.ADMIN_TELEGRAM_ID is not None and message.from_user.id == settings.ADMIN_TELEGRAM_ID:
        return False
    return True


router.message.filter(is_client_filter)


def get_client_inline_keyboard() -> InlineKeyboardMarkup:
    """Generates client navigation keyboard with WebAppInfo button."""
    web_app_url = settings.WEBAPP_URL.rstrip("/") + "/app"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Відкрити кабінет проекту",
                    web_app=WebAppInfo(url=web_app_url),
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Детальний статус",
                    callback_data="client_detailed_status",
                ),
                InlineKeyboardButton(
                    text="ℹ️ Допомога",
                    callback_data="client_help",
                ),
            ],
        ]
    )


def format_milestone_status(status: MilestoneStatus) -> str:
    """Returns friendly emoji label for milestone status."""
    match status:
        case MilestoneStatus.APPROVED:
            return "✅ Затверджено"
        case MilestoneStatus.WAITING_APPROVAL:
            return "⏳ Очікує підтвердження"
        case MilestoneStatus.IN_PROGRESS:
            return "🛠 В роботі"
        case MilestoneStatus.LOCKED:
            return "🔒 Заблоковано"
        case _:
            return str(status.value)


@router.message(CommandStart())
async def client_start_handler(message: types.Message) -> None:
    """Handles /start for clients: looks up active project and renders summary card."""
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Клієнт"

    async with async_session_factory() as session:
        # Lookup user and active project
        stmt = (
            select(Project)
            .join(User, Project.client_id == User.id)
            .where(
                User.telegram_id == user_id,
                Project.status == ProjectStatus.ACTIVE,
            )
            .options(selectinload(Project.milestones))
        )
        project = (await session.execute(stmt)).scalar_one_or_none()

    if not project:
        admin_contact = (
            f"@{settings.ADMIN_USERNAME}"
            if settings.ADMIN_USERNAME
            else "розробника"
        )
        text = (
            f"👋 Вітаємо, <b>{first_name}</b>!\n\n"
            f"У вас поки немає активних проектів у системі.\n\n"
            f"Щоб розпочати новий проект або підключити існуючий, зверніться до {admin_contact}."
        )
        await message.answer(text, parse_mode="HTML")
        return

    milestones = sorted(project.milestones, key=lambda m: m.order_index)
    total_count = len(milestones)
    approved_count = sum(1 for m in milestones if m.status == MilestoneStatus.APPROVED)
    progress = round((approved_count / total_count * 100), 1) if total_count > 0 else 0.0

    # Determine current active or waiting milestone
    current_milestone = next(
        (m for m in milestones if m.status in (MilestoneStatus.WAITING_APPROVAL, MilestoneStatus.IN_PROGRESS)),
        milestones[-1] if milestones else None,
    )
    current_title = current_milestone.title if current_milestone else "Не визначено"
    current_status = (
        format_milestone_status(current_milestone.status)
        if current_milestone
        else "—"
    )

    card_text = (
        f"👋 Вітаємо, <b>{first_name}</b>!\n\n"
        f"📁 Проект: <b>{project.title}</b>\n"
        f"💰 Бюджет: <b>{project.budget:,.2f} {project.currency}</b>\n"
        f"📊 Прогрес: <b>{progress}%</b>\n"
        f"📌 Поточний етап: <b>{current_title}</b> ({current_status})\n\n"
        f"<i>Натисніть кнопку нижче, щоб відкрити клієнтський кабінет або переглянути деталі:</i>"
    )

    await message.answer(
        card_text,
        reply_markup=get_client_inline_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("status"))
@router.message(F.text == "📊 Детальний статус")
async def client_status_handler(message: types.Message) -> None:
    """Shows full roadmap of all project milestones with status emojis."""
    user_id = message.from_user.id

    async with async_session_factory() as session:
        stmt = (
            select(Project)
            .join(User, Project.client_id == User.id)
            .where(
                User.telegram_id == user_id,
                Project.status == ProjectStatus.ACTIVE,
            )
            .options(selectinload(Project.milestones))
        )
        project = (await session.execute(stmt)).scalar_one_or_none()

    if not project:
        await message.answer("У вас немає активного проекту для перегляду статусу.")
        return

    milestones = sorted(project.milestones, key=lambda m: m.order_index)
    lines = [f"📊 <b>Таймлайн проекту: {project.title}</b>\n"]

    for m in milestones:
        status_label = format_milestone_status(m.status)
        lines.append(f"#{m.order_index} <b>{m.title}</b> — {m.amount:,.2f} {project.currency}\n   Статус: {status_label}")

    lines.append("\n<i>Затвердження етапів цифровим підписом доступно в кабінеті проекту.</i>")
    await message.answer("\n".join(lines), reply_markup=get_client_inline_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "client_detailed_status")
async def callback_client_status(call: types.CallbackQuery) -> None:
    """Handles callback query for detailed status button."""
    await call.answer()
    if call.message and isinstance(call.message, types.Message):
        await client_status_handler(call.message)


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Допомога")
async def client_help_handler(message: types.Message) -> None:
    """Shows help instructions for clients."""
    admin_contact = f"@{settings.ADMIN_USERNAME}" if settings.ADMIN_USERNAME else "розробника"
    help_text = (
        "ℹ️ <b>Як користуватися Client Portal:</b>\n\n"
        "1. <b>🚀 Відкрити кабінет проекту:</b>\n"
        "   Запускає Telegram Mini App з інтерактивним таймлайном робіт.\n\n"
        "2. <b>✍️ Затвердження етапів:</b>\n"
        "   Коли етап переходить у статус <i>«Очікує підтвердження»</i>, відкрийте його в кабінеті "
        "і поставте цифровий підпис у полі Canvas. Після цього автоматично сформується акт робіт.\n\n"
        "3. <b>💬 Правки та питання:</b>\n"
        "   У кабінеті натисніть кнопку <i>«Додати тікет»</i>, щоб зафіксувати побажання або баги.\n\n"
        f"Зв'язок з розробником: {admin_contact}"
    )
    await message.answer(help_text, parse_mode="HTML")


@router.callback_query(F.data == "client_help")
async def callback_client_help(call: types.CallbackQuery) -> None:
    """Handles callback query for client help button."""
    await call.answer()
    if call.message and isinstance(call.message, types.Message):
        await client_help_handler(call.message)
