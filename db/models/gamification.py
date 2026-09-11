"""Gamification, XP, Streaks, Achievements, and Vibe tracking models."""

import uuid
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin


class XPTransaction(Base, TimestampMixin):
    """Audit ledger for every point of XP awarded or deducted."""
    __tablename__ = "xp_transactions"

    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(150), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="homework", nullable=False)  # homework, attendance, streak, bonus


class Streak(Base, TimestampMixin):
    """Daily learning streak tracking for students."""
    __tablename__ = "streaks"

    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_activity_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    freeze_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # Streak freeze count


class Achievement(Base, TimestampMixin):
    """Catalog of badges and achievements available in the platform."""
    __tablename__ = "achievements"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title_ru: Mapped[str] = mapped_column(String(100), nullable=False)
    title_uz: Mapped[str] = mapped_column(String(100), nullable=False)
    description_ru: Mapped[str] = mapped_column(Text, nullable=False)
    description_uz: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str] = mapped_column(String(50), default="award", nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=50, nullable=False)


class UserAchievement(Base, TimestampMixin):
    """Bridge table tracking unlocked achievements per user."""
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id: Mapped[str] = mapped_column(String(36), ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False, index=True)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    achievement = relationship("Achievement")


class VibeEntry(Base, TimestampMixin):
    """Student daily emotional/learning vibe check."""
    __tablename__ = "vibe_entries"
    __table_args__ = (UniqueConstraint("student_id", "entry_date", name="uq_student_vibe_date"),)

    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    vibe_type: Mapped[str] = mapped_column(String(30), nullable=False)  # energized, focused, neutral, tired, stressed
    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    entry_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class TeacherPrivateNote(Base, TimestampMixin):
    """Private observations by teachers that are never shared with students."""
    __tablename__ = "teacher_private_notes"

    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id: Mapped[str] = mapped_column(String(36), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
