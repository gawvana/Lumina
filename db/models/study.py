"""Study tools: Spaced Repetition Flashcards and Mastery Skill Tree."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin


class FlashcardSet(Base, TimestampMixin):
    """A collection of flashcards created for a specific subject/topic."""
    __tablename__ = "flashcard_sets"

    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    cards = relationship("FlashcardItem", back_populates="flashcard_set", cascade="all, delete-orphan")


class FlashcardItem(Base, TimestampMixin):
    """Individual card with front, back, and optional hint."""
    __tablename__ = "flashcard_items"

    set_id: Mapped[str] = mapped_column(String(36), ForeignKey("flashcard_sets.id", ondelete="CASCADE"), nullable=False, index=True)
    front_text: Mapped[str] = mapped_column(Text, nullable=False)
    back_text: Mapped[str] = mapped_column(Text, nullable=False)
    hint_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    flashcard_set = relationship("FlashcardSet", back_populates="cards")


class SkillNode(Base, TimestampMixin):
    """Curriculum mastery skill node inside a subject skill tree."""
    __tablename__ = "skill_nodes"

    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    title_ru: Mapped[str] = mapped_column(String(150), nullable=False)
    title_uz: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prerequisite_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("skill_nodes.id", ondelete="SET NULL"), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class StudentSkill(Base, TimestampMixin):
    """Tracks a student's percentage mastery for a skill node."""
    __tablename__ = "student_skills"
    __table_args__ = (UniqueConstraint("student_id", "skill_node_id", name="uq_student_skill_node"),)

    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_node_id: Mapped[str] = mapped_column(String(36), ForeignKey("skill_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    mastery_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0 to 100
