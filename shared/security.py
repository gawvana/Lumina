"""Security utilities for Telegram WebApp initData validation and JWT tokens."""

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl, unquote

import os
from dotenv import load_dotenv
import jwt

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "lumina-dev-super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", str(60 * 24 * 7)))


def validate_telegram_init_data(
    init_data_raw: str,
    bot_token: str,
    max_age_seconds: int = 86400 * 3,  # 3 days tolerance
) -> Optional[Dict[str, Any]]:
    """
    Cryptographically validates Telegram WebApp initData string using HMAC-SHA256.
    Follows official Telegram specifications:
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not init_data_raw or not bot_token:
        return None

    try:
        parsed_items = dict(parse_qsl(init_data_raw, keep_blank_values=True))
        received_hash = parsed_items.pop("hash", None)
        if not received_hash:
            return None

        # Build data-check-string with remaining items sorted alphabetically
        data_check_string = "\n".join(
            f"{key}={value}" for key, value in sorted(parsed_items.items())
        )

        # Telegram algorithm: secret_key = HMAC_SHA256("WebAppData", bot_token)
        secret_key = hmac.new(
            b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256
        ).digest()

        # Calculated hash = HMAC_SHA256(secret_key, data_check_string)
        calculated_hash = hmac.new(
            secret_key, data_check_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(received_hash, calculated_hash):
            return None

        # Check timestamp expiration
        auth_date = int(parsed_items.get("auth_date", 0))
        if auth_date <= 0:
            return None

        current_time = int(time.time())
        if current_time - auth_date > max_age_seconds:
            return None

        # Parse user JSON if present
        result: Dict[str, Any] = dict(parsed_items)
        if "user" in result:
            try:
                result["user"] = json.loads(unquote(result["user"]))
            except Exception:
                pass

        return result
    except Exception:
        return None


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    secret_key: str = JWT_SECRET_KEY,
) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(
    token: str,
    secret_key: str = JWT_SECRET_KEY,
) -> Optional[Dict[str, Any]]:
    """Decodes and validates a signed JWT access token."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
