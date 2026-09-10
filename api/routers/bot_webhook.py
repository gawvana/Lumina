"""FastAPI router for Telegram Bot Webhook integration (Serverless ready)."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, status
from aiogram import Bot, Dispatcher
from aiogram.types import Update

from bot.config import BOT_TOKEN, WEBAPP_URL
from bot.handlers import start_router

logger = logging.getLogger("lumina.webhook")

router = APIRouter(prefix="/bot", tags=["Telegram Bot Webhook"])

# Initialize Dispatcher with routers
dp = Dispatcher()
dp.include_router(start_router)

# Initialize Bot instance if token exists and looks valid
bot: Optional[Bot] = None
if BOT_TOKEN and ":" in BOT_TOKEN and not BOT_TOKEN.endswith("_LuminaDev"):
    try:
        bot = Bot(token=BOT_TOKEN)
    except Exception as exc:
        logger.warning("Failed to initialize Telegram Bot instance: %s", exc)


@router.post("/webhook")
async def telegram_bot_webhook(request: Request):
    """Receives Telegram Update objects from Telegram servers and passes to aiogram."""
    if not bot:
        # Log and accept to prevent Telegram from repeatedly retrying when token isn't ready
        return {"status": "bot_not_configured"}

    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot=bot, update=update)
        return {"status": "ok"}
    except Exception as exc:
        logger.error("Error processing Telegram update: %s", exc)
        return {"status": "error", "detail": str(exc)}


@router.get("/set-webhook")
async def set_telegram_webhook(url: Optional[str] = None):
    """Configures Telegram servers to send updates to this Vercel deployment."""
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TELEGRAM_BOT_TOKEN is not configured with a valid token in environment variables.",
        )

    webhook_url = url or f"{WEBAPP_URL.rstrip('/')}/api/v1/bot/webhook"
    try:
        result = await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
        info = await bot.get_webhook_info()
        return {
            "success": result,
            "registered_url": webhook_url,
            "webhook_info": {
                "url": info.url,
                "pending_update_count": info.pending_update_count,
                "last_error_message": info.last_error_message,
            },
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Telegram API set_webhook error: {str(exc)}",
        )


@router.get("/webhook-info")
async def get_telegram_webhook_info():
    """Retrieves current Telegram webhook status."""
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
