"""Telegram Bot /start command and deep-link invite handler."""

import html
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from aiogram import Router, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from bot.config import WEBAPP_URL
from shared.i18n import t

router = Router(name="start")


def build_webapp_url(base_url: str, invite_token: str = None) -> str:
    """Safely appends invite token to webapp URL without corrupting existing query parameters."""
    if not invite_token:
        return base_url

    parsed = urlparse(base_url)
    query_dict = parse_qs(parsed.query)
    query_dict["inv"] = [invite_token]
    new_query = urlencode(query_dict, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


@router.message(CommandStart(deep_link=True))
async def handle_start_deep_link(message: types.Message, command: CommandObject):
    """Handles deep-link invites e.g. /start inv_abc123."""
    args = command.args or ""
    lang = (message.from_user.language_code or "ru") if message.from_user else "ru"
    if lang not in ["ru", "uz"]:
        lang = "ru"

    if args.startswith("inv_"):
        invite_token = args.replace("inv_", "").strip()
        webapp_link = build_webapp_url(WEBAPP_URL, invite_token)

        app_title = html.escape(t("common.app_name", lang=lang))
        text = (
            f"🎓 <b>{app_title} — Telegram School OS</b>\n\n"
            f"Вы получили персональное приглашение в школу!\n"
            f"Нажмите кнопку ниже, чтобы войти в систему и активировать профиль."
        ) if lang == "ru" else (
            f"🎓 <b>{app_title} — Telegram School OS</b>\n\n"
            f"Siz maktabga shaxsiy taklifnoma oldingiz!\n"
            f"Tizimga kirish va profilingizni faollashtirish uchun quyidagi tugmani bosing."
        )

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚀 Войти в Lumina OS" if lang == "ru" else "🚀 Lumina OS-ga kirish",
                        web_app=WebAppInfo(url=webapp_link),
                    )
                ]
            ]
        )
        await message.answer(text, reply_markup=kb, parse_mode="HTML")
        return

    await handle_start_standard(message)


@router.message(CommandStart())
async def handle_start_standard(message: types.Message):
    """Standard /start command handler."""
    lang = (message.from_user.language_code or "ru") if message.from_user else "ru"
    if lang not in ["ru", "uz"]:
        lang = "ru"

    app_title = html.escape(t("common.app_name", lang=lang))
    text = (
        f"👋 <b>Добро пожаловать в {app_title}!</b>\n\n"
        f"Lumina — школьная операционная система внутри Telegram:\n"
        f"• 📊 Оценки и домашние задания\n"
        f"• 📅 Умное расписание уроков\n"
        f"• 🔔 Моментальные уведомления\n\n"
        f"Откройте приложение для начала работы:"
    ) if lang == "ru" else (
        f"👋 <b>{app_title} tizimiga xush kelibsiz!</b>\n\n"
        f"Lumina — Telegram ichidagi zamonaviy maktab operatsion tizimi:\n"
        f"• 📊 Baholar va uy vazifalari\n"
        f"• 📅 Dars jadvali\n"
        f"• 🔔 Tezkor bildirishnomalar\n\n"
        f"Boshlash uchun ilovani oching:"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 Открыть Lumina" if lang == "ru" else "📱 Lumina-ni ochish",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ]
        ]
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")
