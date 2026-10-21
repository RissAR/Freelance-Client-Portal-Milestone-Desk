"""Automated verification tests for Phase 4: Frontend Build, Anti-Cache, Static Delivery, and End-to-End API Integration."""

import asyncio
import logging
import os
import re
from httpx import ASGITransport, AsyncClient

from main import app
from src.core.database import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_phase4")


async def run_phase4_tests():
    logger.info("Initializing DB for Phase 4 verification...")
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Test /app route delivery and Anti-Cache headers
        logger.info("[Test 1] Testing /app route and anti-cache headers...")
        res = await client.get("/app")
        assert res.status_code == 200, f"Expected 200 for /app, got {res.status_code}"
        assert "no-cache, no-store, must-revalidate" in res.headers.get("Cache-Control", ""), "Missing Cache-Control header"
        assert res.headers.get("Pragma") == "no-cache", "Missing Pragma header"
        assert res.headers.get("Expires") == "0", "Missing Expires header"
        assert '<div id="root"></div>' in res.text, "Missing #root element in HTML"
        logger.info("PASSED: /app returns 200 with strict anti-cache headers.")

        # 2. Extract asset links from HTML and test static serving
        logger.info("[Test 2] Testing static asset delivery via /assets...")
        js_match = re.search(r'src=["\']\./assets/([^"\']+)["\']', res.text)
        css_match = re.search(r'href=["\']\./assets/([^"\']+)["\']', res.text)

        assert js_match, "Could not find JS asset in /app HTML"
        assert css_match, "Could not find CSS asset in /app HTML"

        js_filename = js_match.group(1)
        css_filename = css_match.group(1)

        # Test /assets/{filename}
        js_res = await client.get(f"/assets/{js_filename}")
        assert js_res.status_code == 200, f"Expected 200 for JS asset, got {js_res.status_code}"
        assert len(js_res.content) > 1000, "JS asset content unexpectedly small"

        css_res = await client.get(f"/assets/{css_filename}")
        assert css_res.status_code == 200, f"Expected 200 for CSS asset, got {css_res.status_code}"
        assert len(css_res.content) > 500, "CSS asset content unexpectedly small"

        # Test /app/assets/{filename} fallback
        app_js_res = await client.get(f"/app/assets/{js_filename}")
        assert app_js_res.status_code == 200, f"Expected 200 for /app/assets fallback, got {app_js_res.status_code}"

        logger.info("PASSED: Static assets (JS & CSS) delivered successfully via /assets and /app/assets.")

        # 3. Test client API integration with mock_client
        logger.info("[Test 3] Testing client API with mock_client auth...")
        client_headers = {"X-Telegram-Init-Data": "mock_client"}
        proj_res = await client.get("/api/client/projects/active", headers=client_headers)
        assert proj_res.status_code == 200, f"Expected 200 for active project, got {proj_res.status_code}"
        proj_data = proj_res.json()
        assert "milestones" in proj_data
        assert "progress_percentage" in proj_data
        logger.info("Active project: '%s', Milestones: %d, Progress: %s%%", proj_data["title"], len(proj_data["milestones"]), proj_data["progress_percentage"])
        logger.info("PASSED: Client API active project fetched successfully.")

        # 4. Test client ticket creation
        logger.info("[Test 4] Testing client ticket creation...")
        ticket_payload = {
            "milestone_id": proj_data["milestones"][0]["id"] if proj_data["milestones"] else None,
            "type": "REVISION",
            "message": "Phase 4 automated test ticket: verify frontend integration",
            "attachment_url": "https://example.com/screenshot.png",
        }
        ticket_res = await client.post("/api/client/tickets", headers=client_headers, json=ticket_payload)
        assert ticket_res.status_code == 201, f"Expected 201, got {ticket_res.status_code}"
        ticket_data = ticket_res.json()
        assert ticket_data["message"] == ticket_payload["message"]
        logger.info("PASSED: Client ticket #%d created successfully.", ticket_data["id"])

        # 5. Test admin API integration with mock_admin
        logger.info("[Test 5] Testing admin API with mock_admin auth...")
        admin_headers = {"X-Telegram-Init-Data": "mock_admin"}
        admin_res = await client.get("/api/admin/projects", headers=admin_headers)
        assert admin_res.status_code == 200, f"Expected 200 for admin projects, got {admin_res.status_code}"
        admin_projects = admin_res.json()
        assert len(admin_projects) > 0, "No projects returned for admin"
        logger.info("PASSED: Admin API projects fetched successfully (%d projects).", len(admin_projects))

        # 6. Test admin ticket resolution
        logger.info("[Test 6] Testing admin ticket status update...")
        patch_res = await client.patch(
            f"/api/admin/tickets/{ticket_data['id']}/status",
            headers=admin_headers,
            json={"status": "RESOLVED"},
        )
        assert patch_res.status_code == 200, f"Expected 200, got {patch_res.status_code}"
        assert patch_res.json()["status"] == "RESOLVED"
        logger.info("PASSED: Admin ticket #%d updated to RESOLVED.", ticket_data["id"])

        # 7. Test milestone approval (if waiting approval milestone exists)
        logger.info("[Test 7] Testing milestone digital signature approval...")
        waiting_milestone = next((m for m in proj_data["milestones"] if m["status"] == "WAITING_APPROVAL"), None)
        if waiting_milestone:
            sig_payload = {
                "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            }
            approve_res = await client.post(
                f"/api/client/milestones/{waiting_milestone['id']}/approve",
                headers=client_headers,
                json=sig_payload,
            )
            assert approve_res.status_code == 200, f"Expected 200, got {approve_res.status_code}"
            assert approve_res.json()["status"] == "APPROVED"
            logger.info("PASSED: Milestone #%d approved with digital signature.", waiting_milestone["id"])

        logger.info("=" * 60)
        logger.info("ALL PHASE 4 FRONTEND & INTEGRATION TESTS PASSED 100%!")
        logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_phase4_tests())
