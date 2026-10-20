"""Asynchronous webhook dispatcher for Make.com scenarios."""

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)


async def send_make_event(event_name: str, payload: dict[str, Any]) -> bool:
    """Dispatches asynchronous event to Make.com webhook.

    If MAKE_WEBHOOK_URL is unset or empty, logs a warning and exits gracefully
    without raising an exception.

    Args:
        event_name: Name of the event (e.g. 'milestone_approved', 'ticket_created').
        payload: Event data dictionary.

    Returns:
        bool: True if dispatched successfully, False otherwise.
    """
    webhook_url = settings.MAKE_WEBHOOK_URL.strip()
    if not webhook_url:
        logger.warning(
            "MAKE_WEBHOOK_URL is not configured. Event '%s' will not be sent to Make.com.",
            event_name,
        )
        return False

    body = {
        "event": event_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=body)
            response.raise_for_status()
            logger.info("Successfully dispatched event '%s' to Make.com", event_name)
            return True
    except Exception as exc:
        logger.error(
            "Error dispatching Make.com event '%s' to %s: %s",
            event_name,
            webhook_url,
            exc,
        )
        return False
