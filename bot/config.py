"""Telegram Bot configuration settings."""

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "123456789:ABCdefGhIJKlmNoPQRstuVWXyz_LuminaDev")
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:8000/app")
