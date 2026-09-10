"""Homework and Homework submissions models."""

from datetime import date, datetime
from typing import Optional
from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin
from shared.enums import HomeworkStatus


class Homework(Base, TimestampMixin):
    __tablename__ = "homework"

    class_id: Mapped[str] = mapped_column(String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id: Mapped[str] = mapped_column(String(36), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Relationships
    class_rel = relationship("Class", back_populates="homework")
    subject = relationship("Subject", back_populates="homework")
    teacher = relationship("Teacher", back_populates="homework")
    lesson = relationship("Lesson", back_populates="homework")
    submissions = relationship("HomeworkSubmission", back_populates="homework", cascade="all, delete-orphan")


class HomeworkSubmission(Base, TimestampMixin):
    __tablename__ = "homework_submissions"
    __table_args__ = (
        UniqueConstraint("homework_id", "student_id", name="uq_homework_student"),
    )

    homework_id: Mapped[str] = mapped_column(String(36), ForeignKey("homework.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default=HomeworkStatus.TODO.value)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    homework = relationship("Homework", back_populates="submissions")
    student = relationship("Student", back_populates="homework_submissions")
