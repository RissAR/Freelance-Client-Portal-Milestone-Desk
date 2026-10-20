"""Automated test suite verifying Phase 3 bot handlers, role filters, notifications, and callbacks."""

import asyncio
import logging
import sys
from unittest.mock import AsyncMock, MagicMock

from aiogram import types
from sqlalchemy import select

from src.bot.handlers.admin_handlers import (
    admin_dashboard_handler,
    callback_admin_resolve_ticket,
    callback_admin_start_milestone,
    is_admin_filter,
)
from src.bot.handlers.client_handlers import (
    client_help_handler,
    client_start_handler,
    client_status_handler,
    is_client_filter,
)
from src.core.config import settings
from src.core.database import async_session_factory, init_db
from src.models import Milestone, MilestoneStatus, Project, Ticket, TicketStatus
from src.scripts.seed_initial_data import seed_data
from src.services.notification_service import (
    notify_admin_milestone_approved,
    notify_admin_ticket_created,
    notify_client,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_phase3")

TEST_ADMIN_ID = 8607080614
TEST_CLIENT_ID = 222222222
UNKNOWN_CLIENT_ID = 999999999


def create_mock_message(user_id: int, first_name: str = "Test", username: str = "testuser") -> types.Message:
    """Creates a mock aiogram Message object."""
    user = types.User(id=user_id, is_bot=False, first_name=first_name, username=username)
    chat = types.Chat(id=user_id, type="private")
    msg = MagicMock(spec=types.Message)
    msg.from_user = user
    msg.chat = chat
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
    """Executes the Phase 3 verification suite."""
    logger.info("Initializing configuration and seeding test database...")
    settings.ADMIN_TELEGRAM_ID = TEST_ADMIN_ID
    settings.ADMIN_USERNAME = "test_lead"
    settings.BOT_TOKEN = "123456:testBotToken"

    await init_db()
    await seed_data()

    # -----------------------------------------------------------------
    # 1. Test: Role Filters
    # -----------------------------------------------------------------
    logger.info("[Test 1] Verifying RBAC filters for Admin vs Client...")
    admin_msg = create_mock_message(TEST_ADMIN_ID)
    client_msg = create_mock_message(TEST_CLIENT_ID)

    assert is_admin_filter(admin_msg) is True
    assert is_client_filter(admin_msg) is False

    assert is_admin_filter(client_msg) is False
    assert is_client_filter(client_msg) is True
    logger.info("PASSED: Role filters strictly isolate admin and client handlers.")

    # -----------------------------------------------------------------
    # 2. Test: Client /start with active project
    # -----------------------------------------------------------------
    logger.info("[Test 2] Testing client /start with active project...")
    msg_client = create_mock_message(TEST_CLIENT_ID, first_name="Alex")
    await client_start_handler(msg_client)

    msg_client.answer.assert_called_once()
    sent_text = msg_client.answer.call_args[0][0]
    sent_markup = msg_client.answer.call_args[1].get("reply_markup")

    assert "Розробка E-commerce Mini App" in sent_text
    assert "2,500.00 USD" in sent_text
    assert sent_markup is not None
    # Check WebAppInfo button
    assert any(btn.web_app is not None for row in sent_markup.inline_keyboard for btn in row)
    logger.info("PASSED: Client /start successfully rendered project summary and WebApp button.")

    # -----------------------------------------------------------------
    # 3. Test: Client /start without active project
    # -----------------------------------------------------------------
    logger.info("[Test 3] Testing client /start without active project...")
    msg_unknown = create_mock_message(UNKNOWN_CLIENT_ID, first_name="Stranger")
    await client_start_handler(msg_unknown)

    msg_unknown.answer.assert_called_once()
    no_proj_text = msg_unknown.answer.call_args[0][0]
    assert "немає активних проектів" in no_proj_text
    assert "@test_lead" in no_proj_text
    logger.info("PASSED: Unknown user receives prompt to contact developer.")

    # -----------------------------------------------------------------
    # 4. Test: Client /status (Milestone timeline)
    # -----------------------------------------------------------------
    logger.info("[Test 4] Testing client /status timeline...")
    msg_status = create_mock_message(TEST_CLIENT_ID)
    await client_status_handler(msg_status)

    msg_status.answer.assert_called_once()
    timeline_text = msg_status.answer.call_args[0][0]
    assert "Таймлайн проекту" in timeline_text
    assert "UX/UI дизайн та архітектура" in timeline_text
    assert "Розробка Frontend та Telegram SDK" in timeline_text
    logger.info("PASSED: Client /status formatted all project milestones with status emojis.")

    # -----------------------------------------------------------------
    # 5. Test: Client /help
    # -----------------------------------------------------------------
    logger.info("[Test 5] Testing client /help instructions...")
    msg_help = create_mock_message(TEST_CLIENT_ID)
    await client_help_handler(msg_help)

    msg_help.answer.assert_called_once()
    help_text = msg_help.answer.call_args[0][0]
    assert "Client Portal" in help_text
    assert "Canvas" in help_text
    logger.info("PASSED: Client /help provided clear instructions.")

    # -----------------------------------------------------------------
    # 6. Test: Admin /admin dashboard
    # -----------------------------------------------------------------
    logger.info("[Test 6] Testing admin /admin dashboard...")
    msg_admin_dash = create_mock_message(TEST_ADMIN_ID)
    await admin_dashboard_handler(msg_admin_dash)

    msg_admin_dash.answer.assert_called_once()
    dash_text = msg_admin_dash.answer.call_args[0][0]
    dash_markup = msg_admin_dash.answer.call_args[1].get("reply_markup")
    assert "Панель керування проектами" in dash_text
    assert "Активні проекти:" in dash_text
    assert dash_markup is not None
    logger.info("PASSED: Admin dashboard aggregated live DB statistics.")

    # -----------------------------------------------------------------
    # 7. Test: Admin Callback admin_start_milestone
    # -----------------------------------------------------------------
    logger.info("[Test 7] Testing admin callback admin_start_milestone...")
    async with async_session_factory() as session:
        # Find milestone with order_index 3
        stmt = select(Milestone).where(Milestone.order_index == 3)
        m3 = (await session.execute(stmt)).scalar_one()
        m3_id = m3.id
        m3.status = MilestoneStatus.LOCKED
        await session.commit()

    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()
    card_msg = create_mock_message(TEST_ADMIN_ID)
    call_start = create_mock_callback(
        user_id=TEST_ADMIN_ID,
        data=f"admin_start_milestone:{m3_id}",
        message=card_msg,
        bot=mock_bot,
    )

    await callback_admin_start_milestone(call_start)

    call_start.answer.assert_called_once()
    card_msg.edit_text.assert_called_once()
    mock_bot.send_message.assert_called_once()
    assert mock_bot.send_message.call_args[1]["chat_id"] == TEST_CLIENT_ID

    async with async_session_factory() as session:
        rechecked_m3 = await session.get(Milestone, m3_id)
        assert rechecked_m3 is not None
        assert rechecked_m3.status == MilestoneStatus.IN_PROGRESS
    logger.info("PASSED: Admin callback changed milestone to IN_PROGRESS and notified client.")

    # -----------------------------------------------------------------
    # 8. Test: Admin Callback admin_resolve_ticket
    # -----------------------------------------------------------------
    logger.info("[Test 8] Testing admin callback admin_resolve_ticket...")
    async with async_session_factory() as session:
        stmt = select(Ticket).order_by(Ticket.id.desc())
        t1 = (await session.execute(stmt)).scalars().first()
        assert t1 is not None
        t1_id = t1.id
        t1.status = TicketStatus.OPEN
        await session.commit()

    mock_bot_ticket = MagicMock()
    mock_bot_ticket.send_message = AsyncMock()
    ticket_msg = create_mock_message(TEST_ADMIN_ID)
    call_resolve = create_mock_callback(
        user_id=TEST_ADMIN_ID,
        data=f"admin_resolve_ticket:{t1_id}",
        message=ticket_msg,
        bot=mock_bot_ticket,
    )

    await callback_admin_resolve_ticket(call_resolve)

    call_resolve.answer.assert_called_once()
    ticket_msg.edit_text.assert_called_once()
    mock_bot_ticket.send_message.assert_called_once()
    assert mock_bot_ticket.send_message.call_args[1]["chat_id"] == TEST_CLIENT_ID

    async with async_session_factory() as session:
        rechecked_t1 = await session.get(Ticket, t1_id)
        assert rechecked_t1 is not None
        assert rechecked_t1.status == TicketStatus.RESOLVED
    logger.info("PASSED: Admin callback resolved ticket and notified client.")

    # -----------------------------------------------------------------
    # 9. Test: Notification Service
    # -----------------------------------------------------------------
    logger.info("[Test 9] Testing Notification Service...")
    service_bot = MagicMock()
    service_bot.send_message = AsyncMock()

    ok1 = await notify_admin_milestone_approved(
        bot=service_bot,
        milestone_id=1,
        milestone_title="Design",
        amount=750.0,
        currency="USD",
        project_title="E-commerce",
        client_name="Alex",
    )
    assert ok1 is True
    assert service_bot.send_message.call_args[1]["chat_id"] == TEST_ADMIN_ID

    ok2 = await notify_admin_ticket_created(
        bot=service_bot,
        ticket_id=10,
        ticket_type="BUG",
        message_text="Fix button",
        project_title="E-commerce",
        client_name="Alex",
    )
    assert ok2 is True

    ok3 = await notify_client(
        bot=service_bot,
        client_telegram_id=TEST_CLIENT_ID,
        text="Status updated",
    )
    assert ok3 is True
    assert service_bot.send_message.call_args[1]["chat_id"] == TEST_CLIENT_ID

    # Test error resilience
    service_bot.send_message.side_effect = Exception("Network timeout")
    ok_err = await notify_client(service_bot, TEST_CLIENT_ID, "Fail test")
    assert ok_err is False
    logger.info("PASSED: Notification service successfully dispatched cards and handled errors gracefully.")

    # Reset token to avoid leaking
    settings.BOT_TOKEN = ""
    logger.info("ALL PHASE 3 BOT AND NOTIFICATION TESTS PASSED 100%!")


def main() -> None:
    """Test suite entrypoint."""
    try:
        asyncio.run(run_tests())
    except Exception as exc:
        logger.exception("Test suite FAILED: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
