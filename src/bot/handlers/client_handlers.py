"""Client and guest handlers for Telegram bot: dashboard, demo cabinet, FAQ, and project links."""

import html
import logging
from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.bot.keyboards.inline import (
    get_client_project_inline_keyboard,
    get_guest_inline_keyboard,
)
from src.bot.keyboards.reply import get_persistent_reply_keyboard
from src.core.config import settings
from src.core.database import async_session_factory
from src.models import Milestone, MilestoneStatus, Project, ProjectStatus, User

logger = logging.getLogger(__name__)

router = Router(name="client_router")


def is_client_filter(event: types.Message | types.CallbackQuery) -> bool:
    """Filter ensuring user is not the configured administrator."""
    if not event.from_user:
        return False
    if settings.ADMIN_TELEGRAM_ID is not None and event.from_user.id == settings.ADMIN_TELEGRAM_ID:
        return False
    return True


router.message.filter(is_client_filter)
router.callback_query.filter(is_client_filter)


def format_milestone_status(status: MilestoneStatus) -> str:
    """Returns friendly label for milestone status."""
    match status:
        case MilestoneStatus.APPROVED:
            return "Затверджено"
        case MilestoneStatus.WAITING_APPROVAL:
            return "Очікує підтвердження"
        case MilestoneStatus.IN_PROGRESS:
            return "В роботі"
        case MilestoneStatus.LOCKED:
            return "Черга"
        case _:
            return str(status.value)


@router.message(CommandStart())
@router.message(F.text.in_({"📱 Головне меню", "Головне меню", "/menu"}))
async def client_start_handler(message: types.Message) -> None:
    """Handles /start and main menu for clients and guests."""
    user_id = message.from_user.id if message.from_user else 0
    first_name = html.escape(message.from_user.first_name) if message.from_user and message.from_user.first_name else "Клієнт"

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

    # Ensure persistent reply keyboard is active
    if message.text and message.text.startswith("/start"):
        await message.answer(
            "<b>Client Portal &amp; Milestone Desk</b> активовано.",
            reply_markup=get_persistent_reply_keyboard(),
            parse_mode="HTML",
        )

    # 1. Flow when client has an active commercial project
    if project:
        milestones = sorted(project.milestones, key=lambda m: m.order_index)
        total_count = len(milestones)
        approved_count = sum(1 for m in milestones if m.status == MilestoneStatus.APPROVED)
        progress = round((approved_count / total_count * 100), 1) if total_count > 0 else 0.0

        current_milestone = next(
            (m for m in milestones if m.status in (MilestoneStatus.WAITING_APPROVAL, MilestoneStatus.IN_PROGRESS)),
            milestones[-1] if milestones else None,
        )
        current_title = html.escape(current_milestone.title) if current_milestone else "Не визначено"
        current_status = format_milestone_status(current_milestone.status) if current_milestone else "—"

        escaped_title = html.escape(project.title)
        card_text = (
            f"Вітаємо, <b>{first_name}</b>!\n\n"
            f"Проект: <b>{escaped_title}</b>\n"
            f"Бюджет: <b>{project.budget:,.2f} {project.currency}</b>\n"
            f"Прогрес: <b>{progress}%</b>\n"
            f"Поточний етап: <b>{current_title}</b> ({current_status})\n\n"
            f"<i>Скористайтеся кнопками нижче для переходу до кабінету, тестового стенду чи зв'язку з розробником:</i>"
        )

        await message.answer(
            card_text,
            reply_markup=get_client_project_inline_keyboard(project),
            parse_mode="HTML",
        )
        return

    # 2. Flow for new guests / portfolio visitors
    admin_tag = f"@{settings.ADMIN_USERNAME}" if settings.ADMIN_USERNAME else "розробника"
    guest_text = (
        f"Вітаємо, <b>{first_name}</b>!\n\n"
        f"Це персональний <b>Client Portal &amp; Milestone Desk</b> — простір прозорого ведення "
        f"діджитал-проектів.\n\n"
        f"<b>Як я працюю з клієнтами:</b>\n"
        f"• <b>Поетапна оплата й прийомка:</b> кожен спринт затверджується цифровим підписом на Canvas.\n"
        f"• <b>Жодна правка не губиться:</b> структуровані тікети замість безладу в повідомленнях.\n"
        f"• <b>Миттєвий доступ:</b> робочий кабінет прямо в Telegram Mini App без зайвих паролів.\n\n"
        f"<i>Спробуйте інтерактивний демо-кабінет або зв'яжіться зі мною ({admin_tag}) для оцінки вашого проекту:</i>"
    )

    await message.answer(
        guest_text,
        reply_markup=get_guest_inline_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("status"))
async def client_status_handler(message: types.Message) -> None:
    """Shows full roadmap of all project milestones with status emojis."""
    user_id = message.from_user.id if message.from_user else 0

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
        await message.answer(
            "У вас поки немає активного проекту для перегляду статусу.",
            reply_markup=get_guest_inline_keyboard(),
        )
        return

    milestones = sorted(project.milestones, key=lambda m: m.order_index)
    escaped_title = html.escape(project.title)
    lines = [f"<b>Таймлайн проекту: {escaped_title}</b>\n"]

    for m in milestones:
        status_label = format_milestone_status(m.status)
        escaped_m_title = html.escape(m.title)
        lines.append(f"#{m.order_index} <b>{escaped_m_title}</b> — {m.amount:,.2f} {project.currency}\n   Статус: {status_label}")

    lines.append("\n<i>Затвердження етапів цифровим підписом доступно в кабінеті проекту.</i>")
    await message.answer(
        "\n".join(lines),
        reply_markup=get_client_project_inline_keyboard(project),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "client_detailed_status")
async def callback_client_status(call: types.CallbackQuery) -> None:
    """Handles callback query for detailed status button."""
    await call.answer()
    if call.message and isinstance(call.message, types.Message):
        await client_status_handler(call.message)


@router.callback_query(F.data == "guest_faq_how_it_works")
async def callback_guest_faq_how_it_works(call: types.CallbackQuery) -> None:
    """Provides detailed FAQ on how projects are managed via Client Portal."""
    await call.answer()
    text = (
        "<b>Як працює Client Portal:</b>\n\n"
        "1. <b>Декомпозиція на етапи:</b> Проект розбивається на чіткі майлстоуни (дизайн, верстка, бекенд, інтеграції).\n"
        "2. <b>Тестовий стенд:</b> Ви бачите живий результат на стейджингу перед кожним затвердженням.\n"
        "3. <b>Цифровий підпис:</b> Прийомка фіксується вашим підписом на Canvas у Mini App, формуючи офіційний акт робіт.\n"
        "4. <b>Тікети та правки:</b> Зауваження додаються у вигляді структурованих карток зі статусами вирішення."
    )
    if call.message and isinstance(call.message, types.Message):
        await call.message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "guest_faq_advantages")
async def callback_guest_faq_advantages(call: types.CallbackQuery) -> None:
    """Explains advantages of Client Portal over Jira/Trello/Chats."""
    await call.answer()
    text = (
        "<b>Чому цей підхід кращий за Trello, Jira чи звичайний чат?</b>\n\n"
        "• <b>Все в одному вікні Telegram:</b> Жодних реєстрацій у сторонніх сервісах чи забутих паролів.\n"
        "• <b>Без «загублених» повідомлень:</b> Правки не тонуть у стрічці переписки — кожне завдання має свій статус.\n"
        "• <b>Прозорість бюджету:</b> Чіткий облік виконаних робіт та наступних оплат у реальному часі.\n"
        "• <b>Дотримання дедлайнів:</b> Автоматичні нагадування про перевірку етапів без нав'язливих дзвінків."
    )
    if call.message and isinstance(call.message, types.Message):
        await call.message.answer(text, parse_mode="HTML")


@router.message(Command("help"))
async def client_help_handler(message: types.Message) -> None:
    """Shows help instructions for clients."""
    admin_contact = f"@{settings.ADMIN_USERNAME}" if settings.ADMIN_USERNAME else "розробника"
    help_text = (
        "<b>Як користуватися Client Portal:</b>\n\n"
        "1. <b>Відкрити кабінет проекту:</b>\n"
        "   Запускає Telegram Mini App з інтерактивним таймлайном робіт.\n\n"
        "2. <b>Затвердження етапів:</b>\n"
        "   Коли етап переходить у статус <i>«Очікує підтвердження»</i>, відкрийте його в кабінеті "
        "і поставте цифровий підпис у полі Canvas. Після цього автоматично формується акт.\n\n"
        "3. <b>Правки та питання:</b>\n"
        "   У кабінеті натисніть кнопку <i>«Додати тікет»</i>, щоб зафіксувати побажання або баги.\n\n"
        f"Зв'язок з розробником: {admin_contact}"
    )
    await message.answer(help_text, parse_mode="HTML")

