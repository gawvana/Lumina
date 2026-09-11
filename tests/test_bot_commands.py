"""Tests for Telegram Bot command handlers: /app, /help, /language, /profile, /grades, /homework, /schedule, /settings."""

from unittest.mock import AsyncMock, MagicMock
import pytest

from bot.handlers.commands import cmd_app, cmd_help, cmd_language, cmd_settings
from bot.handlers.start import handle_start_standard


@pytest.mark.asyncio
async def test_bot_cmd_start():
    message = MagicMock()
    message.from_user = MagicMock(language_code="ru")
    message.answer = AsyncMock()

    await handle_start_standard(message)
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    assert "Добро пожаловать" in args[0]
    assert kwargs.get("reply_markup") is not None


@pytest.mark.asyncio
async def test_bot_cmd_app():
    message = MagicMock()
    message.from_user = MagicMock(language_code="ru")
    message.answer = AsyncMock()

    await cmd_app(message)
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    assert "Lumina" in args[0]
    assert kwargs.get("reply_markup") is not None


@pytest.mark.asyncio
async def test_bot_cmd_help():
    message = MagicMock()
    message.from_user = MagicMock(language_code="ru")
    message.answer = AsyncMock()

    await cmd_help(message)
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    assert "/profile" in args[0]
    assert "/grades" in args[0]
    assert "/homework" in args[0]


@pytest.mark.asyncio
async def test_bot_cmd_language_toggle():
    message = MagicMock()
    message.answer = AsyncMock()

    await cmd_language(message)
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    assert "Русский" in str(kwargs.get("reply_markup"))
    assert "O'zbekcha" in str(kwargs.get("reply_markup"))


@pytest.mark.asyncio
async def test_bot_cmd_settings():
    message = MagicMock()
    message.from_user = MagicMock(language_code="ru")
    message.answer = AsyncMock()

    await cmd_settings(message)
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    assert "Настройки" in args[0]
