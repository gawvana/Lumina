"""Tests for Telegram WebApp initData HMAC-SHA256 signature verification."""

import time
import pytest
from httpx import AsyncClient

from shared.security import validate_telegram_init_data
from tests.conftest import TEST_BOT_TOKEN, generate_test_init_data


@pytest.mark.asyncio
async def test_valid_init_data_signature():
    """Valid Telegram HMAC signature must decode and validate successfully."""
    init_data = generate_test_init_data(
        user_id=1234567,
        first_name="Said",
        last_name="Karimov",
        username="skarimov",
        bot_token=TEST_BOT_TOKEN,
    )
    result = validate_telegram_init_data(init_data, TEST_BOT_TOKEN)
    assert result is not None
    assert "user" in result
    assert result["user"]["id"] == 1234567
    assert result["user"]["first_name"] == "Said"


@pytest.mark.asyncio
async def test_tampered_init_data_rejected():
    """Tampered initData hash must be rejected."""
    init_data = generate_test_init_data(
        user_id=1234567,
        bot_token=TEST_BOT_TOKEN,
        tampered=True,
    )
    result = validate_telegram_init_data(init_data, TEST_BOT_TOKEN)
    assert result is None


@pytest.mark.asyncio
async def test_wrong_bot_token_rejected():
    """Valid initData tested against an incorrect bot token must be rejected."""
    init_data = generate_test_init_data(
        user_id=1234567,
        bot_token=TEST_BOT_TOKEN,
    )
    result = validate_telegram_init_data(init_data, "987654321:WrongBotToken")
    assert result is None


@pytest.mark.asyncio
async def test_expired_init_data_rejected():
    """initData older than allowed threshold must be rejected."""
    expired_time = int(time.time()) - (86400 * 5)  # 5 days old
    init_data = generate_test_init_data(
        user_id=1234567,
        bot_token=TEST_BOT_TOKEN,
        auth_date=expired_time,
    )
    result = validate_telegram_init_data(init_data, TEST_BOT_TOKEN, max_age_seconds=86400)
    assert result is None


@pytest.mark.asyncio
async def test_empty_init_data_rejected():
    """Empty or malformed string must be rejected."""
    assert validate_telegram_init_data("", TEST_BOT_TOKEN) is None
    assert validate_telegram_init_data("foo=bar&baz=1", TEST_BOT_TOKEN) is None
