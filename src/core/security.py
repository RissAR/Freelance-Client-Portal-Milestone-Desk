"""Telegram WebApp initData validation and cryptographic utilities."""

import hashlib
import hmac
import json
import logging
import urllib.parse
from datetime import datetime, timezone
from typing import Any

from src.core.config import settings

logger = logging.getLogger(__name__)


def validate_telegram_init_data(init_data: str, bot_token: str | None = None) -> dict[str, Any]:
    """Validates Telegram WebApp initData query string using HMAC-SHA256 according to Telegram specs.

    Args:
        init_data: Raw initData string from Telegram WebApp SDK.
        bot_token: Telegram bot token. Defaults to settings.BOT_TOKEN.

    Returns:
        dict: Parsed user data containing telegram_id, full_name, username, etc.

    Raises:
        ValueError: If data is invalid, signature mismatch, expired, or token is missing.
    """
    token = bot_token or settings.BOT_TOKEN

    # Dev mock bypass: only allowed when settings.DEBUG is enabled
    if settings.DEBUG and init_data in ("mock_client", "mock_admin"):
        if init_data == "mock_client":
            return {
                "telegram_id": 222222222,
                "username": "alex_client",
                "full_name": "Alex Client",
                "first_name": "Alex",
                "last_name": "Client",
                "is_mock": True,
            }
        if init_data == "mock_admin":
            return {
                "telegram_id": 111111111,
                "username": "freelance_lead",
                "full_name": "Freelance Lead (Admin)",
                "first_name": "Freelance",
                "last_name": "Lead",
                "is_mock": True,
            }

    if not token:
        raise ValueError("BOT_TOKEN is not configured. Cannot validate Telegram initData.")

    if not init_data:
        raise ValueError("Empty initData provided.")

    try:
        parsed_qsl = urllib.parse.parse_qsl(init_data, keep_blank_values=True)
    except Exception as e:
        raise ValueError(f"Failed to parse initData query string: {e}") from e

    data_dict = dict(parsed_qsl)
    received_hash = data_dict.pop("hash", None)
    if not received_hash:
        raise ValueError("Missing 'hash' in Telegram initData.")

    # 1. Sort remaining key-values alphabetically
    data_check_list = [f"{k}={v}" for k, v in sorted(data_dict.items(), key=lambda x: x[0])]
    data_check_string = "\n".join(data_check_list)

    # 2. secret_key = HMAC_SHA256(b"WebAppData", bot_token)
    secret_key = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()

    # 3. calculated_hash = HMAC_SHA256(secret_key, data_check_string).hexdigest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    # 4. Constant-time comparison
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Invalid Telegram initData signature: hash mismatch.")

    # 5. Check auth_date freshness (must be <= 24 hours old / 86400 seconds)
    auth_date_raw = data_dict.get("auth_date")
    if auth_date_raw:
        try:
            auth_timestamp = int(auth_date_raw)
            current_timestamp = int(datetime.now(timezone.utc).timestamp())
            if current_timestamp - auth_timestamp > 86400:
                raise ValueError("Telegram initData expired: signature is older than 24 hours.")
        except (TypeError, ValueError) as exc:
            if "expired" in str(exc):
                raise
            logger.warning("Unparseable auth_date in initData: %s", auth_date_raw)

    # 6. Extract user data
    user_payload: dict[str, Any] = {}
    if "user" in data_dict:
        try:
            user_payload = json.loads(data_dict["user"])
        except json.JSONDecodeError as e:
            raise ValueError("Malformed JSON in 'user' field of initData.") from e

    telegram_id = user_payload.get("id")
    if not telegram_id:
        raise ValueError("User ID missing from initData payload.")

    first_name = user_payload.get("first_name", "")
    last_name = user_payload.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip() or user_payload.get("username") or "Telegram User"

    return {
        "telegram_id": int(telegram_id),
        "username": user_payload.get("username"),
        "first_name": first_name,
        "last_name": last_name,
        "full_name": full_name,
        "auth_date": data_dict.get("auth_date"),
        "raw_user": user_payload,
        "is_mock": False,
    }


def create_test_init_data(user_dict: dict[str, Any], bot_token: str, auth_date: int | None = None) -> str:
    """Helper for testing: creates a cryptographically valid initData string.

    Args:
        user_dict: Dictionary with user fields (e.g. {"id": 12345, "first_name": "Test"}).
        bot_token: Bot token to sign with.
        auth_date: Optional unix timestamp. Defaults to current timestamp.

    Returns:
        str: Encoded Telegram initData string with valid 'hash'.
    """
    user_json = json.dumps(user_dict, separators=(",", ":"))
    current_ts = int(datetime.now(timezone.utc).timestamp())
    params = {
        "auth_date": str(auth_date or current_ts),
        "query_id": "AAHdF6IQAAAAAN0XohD72u_6",
        "user": user_json,
    }
    data_check_list = [f"{k}={v}" for k, v in sorted(params.items(), key=lambda x: x[0])]
    data_check_string = "\n".join(data_check_list)

    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    params["hash"] = calc_hash

    return urllib.parse.urlencode(params)
