"""Automated test suite verifying Phase 3+ bot features: persistent reply keyboard, inline actions, guest demo, and security."""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pydantic
from aiogram import types
from sqlalchemy import select

from src.bot.handlers.admin_handlers import (
    admin_dashboard_handler,
    callback_admin_all_projects,
    callback_admin_open_tickets,
    callback_admin_refresh_dashboard,
    callback_admin_remind_client,
    callback_admin_resolve_ticket,
    callback_admin_start_milestone,
    callback_admin_waiting_milestones,
    is_admin_filter,
)
from src.bot.handlers.client_handlers import (
    callback_client_status,
    callback_guest_faq_advantages,
    callback_guest_faq_how_it_works,
    client_help_handler,
    client_start_handler,
    client_status_handler,
    is_client_filter,
)
from src.bot.keyboards.inline import (
    get_client_project_inline_keyboard,
    get_guest_inline_keyboard,
)
from src.bot.keyboards.reply import get_persistent_reply_keyboard
from src.core.config import settings
from src.core.database import async_session_factory, init_db
from src.core.security import create_test_init_data, validate_telegram_init_data
from src.models import Milestone, MilestoneStatus, Project, Ticket, TicketStatus
from src.schemas.milestone import MilestoneApproveIn
from src.schemas.ticket import TicketCreateIn
from src.scripts.seed_initial_data import seed_data
from src.services.notification_service import (
    notify_admin_milestone_approved,
    notify_admin_ticket_created,
    notify_client,
    notify_client_milestone_reminder,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_phase3")

TEST_ADMIN_ID = 8607080614
TEST_CLIENT_ID = 222222222
UNKNOWN_CLIENT_ID = 999999999
MOCK_BOT_TOKEN = "mock_test_token"


def create_mock_message(user_id: int, text: str = "/start", first_name: str = "Test", username: str = "testuser") -> types.Message:
    """Creates a mock aiogram Message object."""
    user = types.User(id=user_id, is_bot=False, first_name=first_name, username=username)
    chat = types.Chat(id=user_id, type="private")
    msg = MagicMock(spec=types.Message)
    msg.from_user = user
    msg.chat = chat
    msg.text = text
    msg.answer = AsyncMock()
    msg.html_text = "<b>Previous text</b>"
    msg.edit_text = AsyncMock()
    return msg


def create_mock_callback(user_id: int, data: str, message: types.Message, bot: MagicMock) -> types.CallbackQuery:
    """Creates a mock aiogram CallbackQuery object."""
    user = types.User(id=user_id, is_bot=False, first_name="Admin", username="admin")
    call = MagicMock(spec=types.CallbackQuery)
    call.from_user = user
    call.data = data
    call.message = message
    call.bot = bot
    call.answer = AsyncMock()
    return call


async def run_tests() -> None:
    """Executes the Phase 3+ verification suite."""
    logger.info("Initializing configuration and test database...")
    settings.ADMIN_TELEGRAM_ID = TEST_ADMIN_ID
    settings.ADMIN_USERNAME = "test_lead"
    settings.BOT_TOKEN = MOCK_BOT_TOKEN
    settings.DEBUG = False

    await init_db()
    await seed_data()

    # -----------------------------------------------------------------
    # 1. Test: Persistent Reply Keyboard
    # -----------------------------------------------------------------
    logger.info("[Test 1] Testing persistent reply keyboard structure...")
    reply_kb = get_persistent_reply_keyboard()
    assert reply_kb.is_persistent is True
    assert reply_kb.resize_keyboard is True
    assert len(reply_kb.keyboard[0]) == 2
    assert reply_kb.keyboard[0][0].text == "🚀 Відкрити кабінет"
    assert reply_kb.keyboard[0][0].web_app is not None
    assert reply_kb.keyboard[0][1].text == "📱 Головне меню"
    logger.info("PASSED: Persistent reply keyboard created with expected buttons.")

    # -----------------------------------------------------------------
    # 2. Test: Client Inline Keyboard (with Staging & Figma)
    # -----------------------------------------------------------------
    logger.info("[Test 2] Testing client inline keyboard with dynamic links...")
    async with async_session_factory() as session:
        stmt = select(Project).where(Project.client_id == 2)
        project = (await session.execute(stmt)).scalars().first()
        assert project is not None
        assert project.staging_url is not None
        assert project.figma_url is not None

        client_kb = get_client_project_inline_keyboard(project)
        all_buttons = [btn for row in client_kb.inline_keyboard for btn in row]
        button_texts = [b.text for b in all_buttons]

        assert "🚀 Відкрити кабінет проекту" in button_texts
        assert "🌐 Тестовий стенд" in button_texts
        assert "🎨 Figma" in button_texts
        assert "📊 Детальний статус" in button_texts
        assert "💬 Написати розробнику" in button_texts
    logger.info("PASSED: Client inline keyboard contains Staging, Figma, and Contact buttons.")

    # -----------------------------------------------------------------
    # 3. Test: Guest Menu & FAQ Callbacks
    # -----------------------------------------------------------------
    logger.info("[Test 3] Testing guest menu and FAQ...")
    guest_kb = get_guest_inline_keyboard()
    guest_buttons = [btn.text for row in guest_kb.inline_keyboard for btn in row]
    assert "🔍 Відкрити Демо-кабінет" in guest_buttons
    assert "💬 Обговорити проект / Замовити" in guest_buttons
    assert "ℹ️ Як це працює" in guest_buttons
    assert "⭐ Чому не Trello/Jira?" in guest_buttons

    # Test unknown user receives guest screen
    msg_unknown = create_mock_message(UNKNOWN_CLIENT_ID, first_name="Stranger")
    await client_start_handler(msg_unknown)
    msg_unknown.answer.assert_called()
    assert any("Демо-кабінет" in str(call_arg) for call_arg in msg_unknown.answer.call_args_list)

    # Test FAQ callbacks
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()
    call_msg = create_mock_message(UNKNOWN_CLIENT_ID)

    faq_call1 = create_mock_callback(UNKNOWN_CLIENT_ID, "guest_faq_how_it_works", call_msg, mock_bot)
    await callback_guest_faq_how_it_works(faq_call1)
    faq_call1.answer.assert_called_once()
    call_msg.answer.assert_called()
    assert "Як працює Client Portal" in call_msg.answer.call_args[0][0]

    call_msg2 = create_mock_message(UNKNOWN_CLIENT_ID)
    faq_call2 = create_mock_callback(UNKNOWN_CLIENT_ID, "guest_faq_advantages", call_msg2, mock_bot)
    await callback_guest_faq_advantages(faq_call2)
    faq_call2.answer.assert_called_once()
    call_msg2.answer.assert_called()
    assert "Trello" in call_msg2.answer.call_args[0][0]
    logger.info("PASSED: Guest flow and interactive FAQ verified.")

    # -----------------------------------------------------------------
    # 4. Test: Admin Queues (Waiting milestones, Open tickets, All projects)
    # -----------------------------------------------------------------
    logger.info("[Test 4] Testing admin interactive queues...")
    admin_msg = create_mock_message(TEST_ADMIN_ID, text="/admin")
    await admin_dashboard_handler(admin_msg)
    admin_msg.answer.assert_called()

    # Admin refresh dashboard
    call_refresh = create_mock_callback(TEST_ADMIN_ID, "admin_refresh_dashboard", admin_msg, mock_bot)
    await callback_admin_refresh_dashboard(call_refresh)
    call_refresh.answer.assert_called_once()
    admin_msg.edit_text.assert_called_once()

    # Admin waiting milestones
    admin_call_msg = create_mock_message(TEST_ADMIN_ID)
    call_waiting = create_mock_callback(TEST_ADMIN_ID, "admin_waiting_milestones", admin_call_msg, mock_bot)
    await callback_admin_waiting_milestones(call_waiting)
    call_waiting.answer.assert_called_once()

    # Admin remind client
    async with async_session_factory() as session:
        stmt = select(Milestone).where(Milestone.order_index == 2)
        m2 = (await session.execute(stmt)).scalar_one()
        m2_id = m2.id

    remind_msg = create_mock_message(TEST_ADMIN_ID)
    call_remind = create_mock_callback(TEST_ADMIN_ID, f"admin_remind_client:{m2_id}", remind_msg, mock_bot)
    await callback_admin_remind_client(call_remind)
    call_remind.answer.assert_called_once()
    mock_bot.send_message.assert_called()
    assert "готовий до перегляду" in mock_bot.send_message.call_args[1]["text"]

    # Admin open tickets
    call_tickets = create_mock_callback(TEST_ADMIN_ID, "admin_open_tickets", admin_call_msg, mock_bot)
    await callback_admin_open_tickets(call_tickets)
    call_tickets.answer.assert_called_once()

    # Admin all projects
    call_projects = create_mock_callback(TEST_ADMIN_ID, "admin_all_projects", admin_call_msg, mock_bot)
    await callback_admin_all_projects(call_projects)
    call_projects.answer.assert_called_once()
    logger.info("PASSED: Admin interactive queues and remind action verified.")

    # -----------------------------------------------------------------
    # 5. Test: HTML Escaping in Notification Service
    # -----------------------------------------------------------------
    logger.info("[Test 5] Testing HTML escaping in notifications...")
    mock_notif_bot = MagicMock()
    mock_notif_bot.send_message = AsyncMock()

    await notify_admin_ticket_created(
        bot=mock_notif_bot,
        ticket_id=99,
        ticket_type="BUG",
        message_text="<b>Dangerous</b> & <script>alert(1)</script>",
        project_title="Test <Project>",
        client_name="O'Connor <Client>",
    )
    sent_text = mock_notif_bot.send_message.call_args[1]["text"]
    assert "&lt;script&gt;" in sent_text
    assert "<script>" not in sent_text
    assert "&lt;Project&gt;" in sent_text
    logger.info("PASSED: User inputs properly escaped with html.escape.")

    # -----------------------------------------------------------------
    # 6. Test: Security Hardening (auth_date, signature size, attachment URL)
    # -----------------------------------------------------------------
    logger.info("[Test 6] Testing security hardening...")

    # 6.1. auth_date expiration (> 24 hours)
    old_timestamp = int(datetime.now(timezone.utc).timestamp()) - 100_000
    expired_init_data = create_test_init_data(
        {"id": 12345, "first_name": "Test"},
        MOCK_BOT_TOKEN,
        auth_date=old_timestamp,
    )
    try:
        validate_telegram_init_data(expired_init_data, MOCK_BOT_TOKEN)
        assert False, "Should have raised ValueError on expired auth_date"
    except ValueError as e:
        assert "expired" in str(e).lower()
        logger.info("PASSED: Expired auth_date (> 24h) rejected successfully.")

    # 6.2. signature_data length limit (max 200,000 chars)
    valid_sig = "a" * 1000
    too_large_sig = "a" * 200_001
    MilestoneApproveIn(signature_data=valid_sig)
    try:
        MilestoneApproveIn(signature_data=too_large_sig)
        assert False, "Should have rejected signature_data > 200_000 chars"
    except pydantic.ValidationError:
        logger.info("PASSED: Signature size limit (200 KB) enforced.")

    # 6.3. attachment_url scheme validation (http/https only)
    TicketCreateIn(message="Test message", attachment_url="https://example.com/file.png")
    TicketCreateIn(message="Test message", attachment_url="http://example.com/file.png")
    try:
        TicketCreateIn(message="Test message", attachment_url="javascript:alert(1)")
        assert False, "Should have rejected javascript: URL"
    except pydantic.ValidationError:
        logger.info("PASSED: attachment_url protocol validation enforced.")

    # Reset test bot token to default empty string to uphold Zero Secrets Leak
    settings.BOT_TOKEN = ""
    settings.ADMIN_TELEGRAM_ID = None
    logger.info("ALL PHASE 3+ BOT, KEYBOARD, AND SECURITY TESTS PASSED 100%!")


def main() -> None:
    """CLI test entrypoint."""
    try:
        asyncio.run(run_tests())
    except Exception as exc:
        logger.exception("Test suite FAILED: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
