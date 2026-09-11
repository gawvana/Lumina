"""FastAPI router for Telegram Bot Webhook integration (Serverless ready and secured)."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from aiogram import Bot, Dispatcher
from aiogram.types import Update

from api.dependencies import require_roles
from bot.handlers import start_router
from db.models.user import User
from shared.config import settings
from shared.enums import UserRole

logger = logging.getLogger("lumina.webhook")

router = APIRouter(prefix="/bot", tags=["Telegram Bot Webhook"])

# Initialize Dispatcher with routers
dp = Dispatcher()
dp.include_router(start_router)

# Initialize Bot instance if token exists and looks valid
bot: Optional[Bot] = None
if settings.TELEGRAM_BOT_TOKEN and ":" in settings.TELEGRAM_BOT_TOKEN:
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    except Exception as exc:
        logger.warning("Failed to initialize Telegram Bot instance: %s", exc)


@router.post("/webhook")
async def telegram_bot_webhook(request: Request):
    """Receives Telegram Update objects securely with secret token verification."""
    # Verify Telegram Webhook Secret Token if configured
    if settings.TELEGRAM_WEBHOOK_SECRET:
        secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret_header != settings.TELEGRAM_WEBHOOK_SECRET:
            logger.warning("Rejected Telegram webhook request: invalid or missing secret token header.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid secret token",
            )

    if not bot:
        return {"status": "bot_not_configured"}

    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot=bot, update=update)
        return {"status": "ok"}
    except Exception as exc:
        logger.error("Error processing Telegram update: %s", exc)
        return {"status": "error", "detail": "Internal update processing error"}


@router.post("/set-webhook")
async def set_telegram_webhook(
    url: Optional[str] = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Configures Telegram servers to send updates to this deployment.
    STRICTLY RESTRICTED TO ADMINS to prevent webhook hijacking.
    """
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TELEGRAM_BOT_TOKEN is not configured in environment variables.",
        )

    webhook_url = url or f"{settings.WEBAPP_URL.rstrip('/')}/api/v1/bot/webhook"
    try:
        set_webhook_kwargs = {"url": webhook_url, "drop_pending_updates": True}
        if settings.TELEGRAM_WEBHOOK_SECRET:
            set_webhook_kwargs["secret_token"] = settings.TELEGRAM_WEBHOOK_SECRET

        result = await bot.set_webhook(**set_webhook_kwargs)
        info = await bot.get_webhook_info()
        return {
            "success": result,
            "registered_url": webhook_url,
            "webhook_info": {
                "url": info.url,
                "pending_update_count": info.pending_update_count,
                "last_error_message": info.last_error_message,
                "has_custom_certificate": info.has_custom_certificate,
            },
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Telegram API set_webhook error: {str(exc)}",
        )


@router.get("/webhook-info")
async def get_telegram_webhook_info(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Retrieves current Telegram webhook status. Restricted to Admins."""
    if not bot:
        return {"status": "bot_not_configured", "token_configured": False}

    try:
        info = await bot.get_webhook_info()
        me = await bot.get_me()
        return {
            "status": "active",
            "bot_username": me.username,
            "webhook_url": info.url,
            "pending_update_count": info.pending_update_count,
            "last_error_message": info.last_error_message,
        }
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
