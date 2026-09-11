"""Gamification, XP Transactions, Streaks, and Achievement Service."""

from datetime import date, datetime, timezone, timedelta
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.gamification import Achievement, Streak, UserAchievement, VibeEntry, XPTransaction
from db.models.user import Student

logger = logging.getLogger("lumina.xp")

# XP Thresholds for Levels: Level = 1 + (XP // 200)
def calculate_level_from_xp(total_xp: int) -> int:
    return max(1, 1 + (total_xp // 200))


async def award_xp(
    db: AsyncSession,
    school_id: str,
    student_id: str,
    amount: int,
    reason: str,
    source: str = "activity",
) -> Dict[str, Any]:
    """Records an XP transaction and increments the student's total XP and level."""
    tx = XPTransaction(
        school_id=school_id,
        student_id=student_id,
        amount=amount,
        reason=reason,
        source=source,
    )
    db.add(tx)

    # Fetch student and update cached XP/Level
    stmt = select(Student).where(Student.id == student_id)
    student = (await db.execute(stmt)).scalars().first()
    new_level = 1
    total_xp = amount
    if student:
        student.xp = max(0, student.xp + amount)
        student.level = calculate_level_from_xp(student.xp)
        new_level = student.level
        total_xp = student.xp

    await db.commit()
    return {"amount": amount, "total_xp": total_xp, "level": new_level, "reason": reason}


async def get_or_create_streak(db: AsyncSession, student_id: str) -> Streak:
    """Gets or initializes streak record for a student."""
    stmt = select(Streak).where(Streak.student_id == student_id)
    streak = (await db.execute(stmt)).scalars().first()
    if not streak:
        streak = Streak(
            student_id=student_id,
            current_streak=1,
            longest_streak=1,
            last_activity_date=date.today(),
            freeze_count=1,
        )
        db.add(streak)
        await db.commit()
        await db.refresh(streak)
    return streak


async def record_daily_activity(db: AsyncSession, student_id: str) -> Streak:
    """Updates daily streak progression with grace period rules."""
    streak = await get_or_create_streak(db, student_id)
    today = date.today()

    if streak.last_activity_date == today:
        return streak  # Already recorded today

    yesterday = today - timedelta(days=1)
    if streak.last_activity_date == yesterday:
        # Continued streak
        streak.current_streak += 1
        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
        streak.last_activity_date = today
    elif (today - streak.last_activity_date).days == 2 and streak.freeze_count > 0:
        # Used a freeze
        streak.freeze_count -= 1
        streak.current_streak += 1
        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
        streak.last_activity_date = today
    else:
        # Streak broken
        streak.current_streak = 1
        streak.last_activity_date = today

    await db.commit()
    await db.refresh(streak)
    return streak


async def seed_default_achievements_if_needed(db: AsyncSession) -> None:
    """Ensures base catalog of badges exists in database."""
    defaults = [
        ("first_grade", "Первая оценка", "Birinchi baho", "Получена первая оценка в системе", "Tizimda birinchi baho olindi", "award", 50),
        ("perfect_streak", "Неделя без пропусков", "Bir hafta to'liq davomat", "7 дней активного обучения подряд", "Ketma-ket 7 kun faol o'qish", "flame", 100),
        ("homework_hero", "Мастер домашки", "Uy vazifasi ustasi", "Сдано 5 домашних заданий вовремя", "5 ta uy vazifasi o'z vaqtida topshirildi", "check-circle", 100),
        ("top_gpa", "Отличник", "A'lochi", "Средний балл выше 4.5", "O'rtacha ball 4.5 dan yuqori", "star", 150),
    ]
    for code, title_ru, title_uz, desc_ru, desc_uz, icon, xp in defaults:
        stmt = select(Achievement).where(Achievement.code == code)
        if not (await db.execute(stmt)).scalars().first():
            ach = Achievement(
                code=code,
                title_ru=title_ru,
                title_uz=title_uz,
                description_ru=desc_ru,
                description_uz=desc_uz,
                icon=icon,
                xp_reward=xp,
            )
            db.add(ach)
    await db.commit()


async def get_student_gamification_profile(db: AsyncSession, student_id: str) -> Dict[str, Any]:
    """Returns complete gamification stats: XP, Level, Streak, Achievements, and Vibe."""
    await seed_default_achievements_if_needed(db)
    streak = await get_or_create_streak(db, student_id)

    student = (await db.execute(select(Student).where(Student.id == student_id))).scalars().first()
    total_xp = student.xp if student else 0
    level = student.level if student else 1
    xp_for_next_level = level * 200
    current_level_progress = total_xp % 200

    # User achievements
    ach_stmt = (
        select(Achievement)
        .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
        .where(UserAchievement.user_id == student_id)
    )
    user_achievements = (await db.execute(ach_stmt)).scalars().all()

    # Available achievements
    all_stmt = select(Achievement)
    all_achievements = (await db.execute(all_stmt)).scalars().all()

    # Today's vibe
    today_vibe = (
        await db.execute(
            select(VibeEntry).where(VibeEntry.student_id == student_id, VibeEntry.entry_date == date.today())
        )
    ).scalars().first()

    return {
        "xp": total_xp,
        "level": level,
        "current_level_progress": current_level_progress,
        "xp_for_next_level": xp_for_next_level,
        "streak_days": streak.current_streak,
        "longest_streak": streak.longest_streak,
        "freeze_count": streak.freeze_count,
        "today_vibe": today_vibe.vibe_type if today_vibe else None,
        "unlocked_achievements": [
            {"id": a.id, "code": a.code, "title_ru": a.title_ru, "title_uz": a.title_uz, "icon": a.icon, "xp": a.xp_reward}
            for a in user_achievements
        ],
        "all_achievements": [
            {"id": a.id, "code": a.code, "title_ru": a.title_ru, "title_uz": a.title_uz, "desc_ru": a.description_ru, "desc_uz": a.description_uz, "icon": a.icon, "xp": a.xp_reward}
            for a in all_achievements
        ],
        "achievements": [
            {"id": a.id, "code": a.code, "title_ru": a.title_ru, "title_uz": a.title_uz, "icon": a.icon, "xp": a.xp_reward}
            for a in all_achievements
        ],
    }
