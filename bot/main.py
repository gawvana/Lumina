"""Lumina Telegram Bot entrypoint using aiogram 3.x."""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN
from bot.handlers import start_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lumina.bot")


async def main():
    """Initializes and runs the Telegram Bot polling loop."""
    logger.info("Starting Lumina Telegram Bot...")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Register handlers
    dp.include_router(start_router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
