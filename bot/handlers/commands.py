"""Comprehensive Bot Commands Handler: /app, /profile, /grades, /homework, /schedule, /settings, /language, /help."""

import html
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.config import WEBAPP_URL
from db.models.academic import Lesson, Subject
from db.models.grading import Grade
from db.models.homework import Homework
from db.models.user import Student, User
from db.session import AsyncSessionLocal
from shared.enums import UserRole
from shared.i18n import t

router = Router(name="commands")


def get_user_lang(message: types.Message) -> str:
    lang = (message.from_user.language_code or "ru") if message.from_user else "ru"
    return "uz" if lang.startswith("uz") else "ru"


@router.message(Command("app"))
async def cmd_app(message: types.Message):
    """Launches the Lumina Telegram Mini App."""
    lang = get_user_lang(message)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 Открыть Lumina OS" if lang == "ru" else "📱 Lumina OS-ni ochish",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ]
        ]
    )
    text = (
        "🚀 <b>Lumina — Школьная операционная система</b>\n\n"
        "Нажмите кнопку ниже, чтобы открыть полноэкранное рабочее пространство:"
    ) if lang == "ru" else (
        "🚀 <b>Lumina — Maktab operatsion tizimi</b>\n\n"
        "To'liq ekranda ishlash uchun quyidagi tugmani bosing:"
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Displays comprehensive help and bot command guide."""
    lang = get_user_lang(message)
    if lang == "ru":
        text = (
            "📖 <b>Справка по командам Lumina Bot</b>\n\n"
            "• /app — Открыть школьное приложение Mini App\n"
            "• /profile — Мой профиль, уровень и серия дней\n"
            "• /grades — Последние оценки и средний балл\n"
            "• /homework — Домашние задания и дедлайны\n"
            "• /schedule — Расписание занятий на сегодня\n"
            "• /language — Сменить язык интерфейса (RU / UZ)\n"
            "• /settings — Настройки уведомлений и приложения\n"
            "• /help — Данная справка\n\n"
            "Для учителей доступно быстрое выставление оценок и рассадка через Mini App."
        )
    else:
        text = (
            "📖 <b>Lumina Bot buyruqlari bo'yicha qo'llanma</b>\n\n"
            "• /app — Maktab Mini App ilovasini ochish\n"
            "• /profile — Profilim, daraja va ketma-ket kunlar\n"
            "• /grades — Oxirgi baholar va o'rtacha ball\n"
            "• /homework — Uy vazifalari va topshirish muddatlari\n"
            "• /schedule — Bugungi dars jadvali\n"
            "• /language — Tilni o'zgartirish (RU / UZ)\n"
            "• /settings — Bildirishnoma va ilova sozlamalari\n"
            "• /help — Ushbu qo'llanma"
        )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📱 Открыть Mini App" if lang == "ru" else "📱 Mini App-ni ochish", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    """Displays user profile, role, level, and streak."""
    lang = get_user_lang(message)
    tg_id = message.from_user.id if message.from_user else 0

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.telegram_id == tg_id))).scalars().first()
        if not user:
            text = (
                "⚠️ <b>Профиль не найден</b>\n\n"
                "Ваш аккаунт Telegram еще не привязан к Lumina. Войдите через приглашение учителя или откройте приложение:"
            ) if lang == "ru" else (
                "⚠️ <b>Profil topilmadi</b>\n\n"
                "Telegram hisobingiz Lumina-ga ulanmagan. Ilovani oching:"
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📱 Войти в Lumina", web_app=WebAppInfo(url=WEBAPP_URL))]])
            await message.answer(text, reply_markup=kb, parse_mode="HTML")
            return

        student = (await db.execute(select(Student).where(Student.id == user.id))).scalars().first()
        level_str = f" • Lvl {student.level} ({student.xp} XP)" if student else ""

        text = (
            f"👤 <b>Профиль Lumina</b>\n\n"
            f"<b>Имя:</b> {html.escape(user.first_name)} {html.escape(user.last_name or '')}\n"
            f"<b>Роль:</b> <code>{user.role}</code>{level_str}\n"
            f"<b>ID:</b> <code>{user.id[:8]}...</code>\n"
        ) if lang == "ru" else (
            f"👤 <b>Lumina Profili</b>\n\n"
            f"<b>Ism:</b> {html.escape(user.first_name)} {html.escape(user.last_name or '')}\n"
            f"<b>Rol:</b> <code>{user.role}</code>{level_str}\n"
            f"<b>ID:</b> <code>{user.id[:8]}...</code>\n"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📱 Открыть в приложении", web_app=WebAppInfo(url=WEBAPP_URL))]])
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("grades"))
async def cmd_grades(message: types.Message):
    """Displays recent grades summary."""
    lang = get_user_lang(message)
    tg_id = message.from_user.id if message.from_user else 0

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.telegram_id == tg_id))).scalars().first()
        if not user:
            await cmd_app(message)
            return

        stmt = (
            select(Grade)
            .where(Grade.student_id == user.id, Grade.is_active == True)
            .order_by(Grade.created_at.desc())
            .limit(5)
            .options(selectinload(Grade.lesson).selectinload(Lesson.subject))
        )
        grades = (await db.execute(stmt)).scalars().all()

        if not grades:
            text = "📊 <b>Оценок пока нет.</b> Все новые оценки будут приходить сюда мгновенно." if lang == "ru" else "📊 <b>Hozircha baholar yo'q.</b>"
        else:
            lines = [f"• {g.lesson.subject.name if g.lesson and g.lesson.subject else 'Предмет'}: <b>{g.raw_display}</b> ({g.comment or 'Без комментария'})" for g in grades]
            text = "📊 <b>Последние оценки:</b>\n\n" + "\n".join(lines)

        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📱 Полный журнал оценок", web_app=WebAppInfo(url=WEBAPP_URL))]])
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("homework"))
async def cmd_homework(message: types.Message):
    """Displays homework deadlines."""
    lang = get_user_lang(message)
    tg_id = message.from_user.id if message.from_user else 0

    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.telegram_id == tg_id))).scalars().first()
        if not user:
            await cmd_app(message)
            return

        student = (await db.execute(select(Student).where(Student.id == user.id))).scalars().first()
        if not student or not student.class_id:
            text = "📚 <b>Домашние задания</b>\n\nОткройте Lumina Mini App для просмотра заданий."
        else:
            stmt = (
                select(Homework)
                .where(Homework.class_id == student.class_id)
                .order_by(Homework.due_date.asc())
                .limit(4)
                .options(selectinload(Homework.subject))
            )
            hw_items = (await db.execute(stmt)).scalars().all()
            if not hw_items:
                text = "🎉 <b>Все задания выполнены!</b> Новых дедлайнов нет."
            else:
                lines = [f"• <b>{h.subject.name if h.subject else 'Предмет'}</b>: {h.title} (срок: {h.due_date})" for h in hw_items]
                text = "📚 <b>Ближайшие домашние задания:</b>\n\n" + "\n".join(lines)

        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📝 Открыть Домашку в App", web_app=WebAppInfo(url=WEBAPP_URL))]])
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("schedule"))
async def cmd_schedule(message: types.Message):
    """Displays schedule button and guidance."""
    lang = get_user_lang(message)
    text = (
        "📅 <b>Расписание занятий</b>\n\n"
        "Смотрите актуальное расписание уроков, кабинетов и звонков в приложении Lumina:"
    ) if lang == "ru" else (
        "📅 <b>Dars jadvali</b>\n\n"
        "Dars jadvali va xonalar ro'yxatini ilovada ko'ring:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📅 Открыть расписание", web_app=WebAppInfo(url=WEBAPP_URL))]])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("language"))
async def cmd_language(message: types.Message):
    """Allows selecting language directly in Telegram."""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
            ]
        ]
    )
    await message.answer("🌐 Выберите язык интерфейса / Tilni tanlang:", reply_markup=kb)


@router.callback_query(lambda c: c.data and c.data.startswith("lang_"))
async def callback_language(query: types.CallbackQuery):
    """Handles language selection callback."""
    chosen = query.data.replace("lang_", "")
    if chosen == "uz":
        resp = "✅ Til O'zbekchaga o'zgartirildi!"
    else:
        resp = "✅ Язык изменён на Русский!"
    await query.answer(resp)
    await query.message.edit_text(f"{resp}\n\nLumina Mini App: {WEBAPP_URL}")


@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    """Displays settings menu."""
    lang = get_user_lang(message)
    text = (
        "⚙️ <b>Настройки Lumina</b>\n\n"
        "• 🔔 Уведомления: Включены\n"
        "• 🌐 Язык: /language\n"
        "• 🎨 Темная тема: настраивается в Mini App\n"
    ) if lang == "ru" else (
        "⚙️ <b>Lumina Sozlamalari</b>\n\n"
        "• 🔔 Bildirishnomalar: Yoqilgan\n"
        "• 🌐 Til: /language\n"
        "• 🎨 Qorong'i rejim: Mini App orqali sozlanadi\n"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⚙️ Открыть настройки в App", web_app=WebAppInfo(url=WEBAPP_URL))]])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")
