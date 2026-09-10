"""Telegram Bot /start command and deep-link invite handler."""

from aiogram import Router, types
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from bot.config import WEBAPP_URL
from shared.i18n import t

router = Router(name="start")


@router.message(CommandStart(deep_link=True))
async def handle_start_deep_link(message: types.Message, command: CommandObject):
    """Handles deep-link invites e.g. /start inv_abc123."""
    args = command.args or ""
    lang = message.from_user.language_code or "ru"
    if lang not in ["ru", "uz"]:
        lang = "ru"

    if args.startswith("inv_"):
        invite_token = args.replace("inv_", "")
        webapp_link = f"{WEBAPP_URL}?inv={invite_token}"

        text = (
            f"🎓 <b>{t('common.app_name', lang=lang)} — Telegram School OS</b>\n\n"
            f"Вы получили персональное приглашение в школу!\n"
            f"Нажмите кнопку ниже, чтобы войти в систему и активировать профиль."
        ) if lang == "ru" else (
            f"🎓 <b>{t('common.app_name', lang=lang)} — Telegram School OS</b>\n\n"
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
    lang = message.from_user.language_code or "ru"
    if lang not in ["ru", "uz"]:
        lang = "ru"

    text = (
        f"👋 <b>Добро пожаловать в {t('common.app_name', lang=lang)}!</b>\n\n"
        f"Lumina — школьная операционная система внутри Telegram:\n"
        f"• 📊 Оценки и домашние задания\n"
        f"• 📅 Умное расписание уроков\n"
        f"• 🔔 Моментальные уведомления\n\n"
        f"Откройте приложение для начала работы:"
    ) if lang == "ru" else (
        f"👋 <b>{t('common.app_name', lang=lang)} tizimiga xush kelibsiz!</b>\n\n"
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
