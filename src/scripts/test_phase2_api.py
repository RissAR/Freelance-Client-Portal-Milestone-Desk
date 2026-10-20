"""Automated test suite verifying Phase 2 REST API, initData crypto, RBAC, race condition lock, and Make dispatcher."""

import asyncio
import logging
import sys
from httpx import ASGITransport, AsyncClient

from main import app
from src.core.config import settings
from src.core.database import init_db
from src.core.security import create_test_init_data
from src.models.enums import MilestoneStatus, TicketStatus, TicketType
from src.scripts.seed_initial_data import seed_data
from src.services.make_dispatcher import send_make_event

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_phase2")

TEST_BOT_TOKEN = "123456789:AAHtestTokenForPhase2ValidationOnly"


async def run_tests() -> None:
    """Executes all Phase 2 integration and unit tests."""
    logger.info("Setting up test database and configuration...")
    settings.BOT_TOKEN = TEST_BOT_TOKEN
    settings.DEBUG = False
    await init_db()
    await seed_data()

    # Generate cryptographically signed initData
    client_init_data = create_test_init_data(
        {"id": 222222222, "first_name": "Alex", "last_name": "Client", "username": "alex_client"},
        TEST_BOT_TOKEN,
    )
    admin_init_data = create_test_init_data(
        {"id": 111111111, "first_name": "Freelance", "last_name": "Lead", "username": "freelance_lead"},
        TEST_BOT_TOKEN,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # -----------------------------------------------------------------
        # 1. Test: Rejection of invalid initData (401 Unauthorized)
        # -----------------------------------------------------------------
        logger.info("[Test 1] Testing rejection of missing/invalid initData...")
        r_no_header = await client.get("/api/client/projects/active")
        assert r_no_header.status_code == 401, f"Expected 401, got {r_no_header.status_code}"

        r_bad_hash = await client.get(
            "/api/client/projects/active",
            headers={"X-Telegram-Init-Data": client_init_data + "tampered"},
        )
        assert r_bad_hash.status_code == 401, f"Expected 401, got {r_bad_hash.status_code}"
        logger.info("PASSED: 401 Unauthorized for tampered and missing signatures.")

        # -----------------------------------------------------------------
        # 2. Test: Successful authentication via valid HMAC-SHA256 initData
        # -----------------------------------------------------------------
        logger.info("[Test 2] Testing successful authentication via valid initData...")
        r_active = await client.get(
            "/api/client/projects/active",
            headers={"X-Telegram-Init-Data": client_init_data},
        )
        assert r_active.status_code == 200, f"Expected 200, got {r_active.status_code}: {r_active.text}"
        project_data = r_active.json()
        assert project_data["title"] == "Розробка E-commerce Mini App"
        assert len(project_data["milestones"]) == 3
        assert project_data["progress_percentage"] == 33.3  # 1 of 3 approved initially
        logger.info("PASSED: Project retrieval with calculated progress %s%%", project_data["progress_percentage"])

        # -----------------------------------------------------------------
        # 3. Test: Approve milestone #2 (WAITING_APPROVAL -> APPROVED)
        #    and auto-advance milestone #3 (LOCKED -> IN_PROGRESS)
        # -----------------------------------------------------------------
        logger.info("[Test 3] Testing milestone approval and auto-advance of subsequent milestone...")
        milestones = project_data["milestones"]
        m2 = next(m for m in milestones if m["order_index"] == 2)
        m3_initial = next(m for m in milestones if m["order_index"] == 3)
        assert m2["status"] == MilestoneStatus.WAITING_APPROVAL.value
        assert m3_initial["status"] == MilestoneStatus.LOCKED.value

        test_sig = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAPAAAADwCAYAAAA+VemSAAA..."
        r_approve = await client.post(
            f"/api/client/milestones/{m2['id']}/approve",
            headers={"X-Telegram-Init-Data": client_init_data},
            json={"signature_data": test_sig, "device_info": {"browser": "Telegram iOS"}},
        )
        assert r_approve.status_code == 200, f"Expected 200, got {r_approve.status_code}: {r_approve.text}"
        approved_m2 = r_approve.json()
        assert approved_m2["status"] == MilestoneStatus.APPROVED.value
        assert approved_m2["signature_data"] == test_sig

        # Verify project state after approval
        r_after_app = await client.get(
            "/api/client/projects/active",
            headers={"X-Telegram-Init-Data": client_init_data},
        )
        updated_proj = r_after_app.json()
        updated_m3 = next(m for m in updated_proj["milestones"] if m["order_index"] == 3)
        assert updated_m3["status"] == MilestoneStatus.IN_PROGRESS.value, (
            f"Milestone 3 should be IN_PROGRESS, got {updated_m3['status']}"
        )
        assert updated_proj["progress_percentage"] == 66.7  # 2 of 3 approved now
        logger.info("PASSED: Milestone #2 approved; Milestone #3 unlocked to IN_PROGRESS.")

        # -----------------------------------------------------------------
        # 4. Test: Race condition / double approval protection (409 Conflict)
        # -----------------------------------------------------------------
        logger.info("[Test 4] Testing duplicate approval race condition protection (409 Conflict)...")
        r_duplicate = await client.post(
            f"/api/client/milestones/{m2['id']}/approve",
            headers={"X-Telegram-Init-Data": client_init_data},
            json={"signature_data": test_sig},
        )
        assert r_duplicate.status_code == 409, f"Expected 409 Conflict, got {r_duplicate.status_code}"
        assert "already approved" in r_duplicate.json()["detail"].lower()
        logger.info("PASSED: 409 Conflict returned on re-approval attempt.")

        # -----------------------------------------------------------------
        # 5. Test: Client creates ticket
        # -----------------------------------------------------------------
        logger.info("[Test 5] Testing client ticket creation...")
        r_ticket = await client.post(
            "/api/client/tickets",
            headers={"X-Telegram-Init-Data": client_init_data},
            json={
                "milestone_id": m2["id"],
                "type": TicketType.BUG.value,
                "message": "Кнопка замовлення зміщується при горизонтальній орієнтації екрану.",
                "attachment_url": "https://cdn.clientportal.dev/bug-screenshot.png",
            },
        )
        assert r_ticket.status_code == 201, f"Expected 201 Created, got {r_ticket.status_code}"
        ticket_data = r_ticket.json()
        assert ticket_data["status"] == TicketStatus.OPEN.value
        assert ticket_data["milestone_id"] == m2["id"]
        logger.info("PASSED: Ticket created successfully id=%d.", ticket_data["id"])

        # -----------------------------------------------------------------
        # 6. Test: RBAC (Client denied admin access, Admin allowed)
        # -----------------------------------------------------------------
        logger.info("[Test 6] Testing RBAC access controls...")
        r_denied = await client.get(
            "/api/admin/projects",
            headers={"X-Telegram-Init-Data": client_init_data},
        )
        assert r_denied.status_code == 403, f"Expected 403 Forbidden for client, got {r_denied.status_code}"

        r_admin_ok = await client.get(
            "/api/admin/projects",
            headers={"X-Telegram-Init-Data": admin_init_data},
        )
        assert r_admin_ok.status_code == 200, f"Expected 200 for admin, got {r_admin_ok.status_code}"
        assert len(r_admin_ok.json()) >= 1
        logger.info("PASSED: RBAC successfully restricts admin routes.")

        # -----------------------------------------------------------------
        # 7. Test: Admin updates ticket status
        # -----------------------------------------------------------------
        logger.info("[Test 7] Testing admin patch ticket status...")
        r_patch_ticket = await client.patch(
            f"/api/admin/tickets/{ticket_data['id']}/status",
            headers={"X-Telegram-Init-Data": admin_init_data},
            json={"status": TicketStatus.RESOLVED.value},
        )
        assert r_patch_ticket.status_code == 200, f"Expected 200, got {r_patch_ticket.status_code}"
        assert r_patch_ticket.json()["status"] == TicketStatus.RESOLVED.value
        logger.info("PASSED: Admin successfully resolved ticket.")

        # -----------------------------------------------------------------
        # 8. Test: Make Dispatcher graceful handling without configured URL
        # -----------------------------------------------------------------
        logger.info("[Test 8] Testing Make.com dispatcher graceful handling...")
        settings.MAKE_WEBHOOK_URL = ""
        dispatch_result = await send_make_event("test_event", {"foo": "bar"})
        assert dispatch_result is False
        logger.info("PASSED: Make.com dispatcher handled empty webhook URL gracefully without crashing.")

    # Reset test bot token to default empty string to uphold Zero Secrets Leak
    settings.BOT_TOKEN = ""
    logger.info("All Phase 2 API and Security tests PASSED 100%!")


def main() -> None:
    """CLI test suite entrypoint."""
    try:
        asyncio.run(run_tests())
    except Exception as exc:
        logger.exception("Test suite FAILED: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
