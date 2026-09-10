"""Grading system, Grade types, and Grades models."""

from typing import Any, Dict, Optional
from sqlalchemy import Boolean, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin
from shared.enums import GradeSource, GradingSystemType


class GradingSystem(Base, TimestampMixin):
    __tablename__ = "grading_systems"

    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    system_type: Mapped[str] = mapped_column(String(30), default=GradingSystemType.POINTS_5.value)
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    school = relationship("School", back_populates="grading_systems")


class GradeType(Base, TimestampMixin):
    __tablename__ = "grade_types"

    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    # Relationships
    grades = relationship("Grade", back_populates="grade_type")


class Grade(Base, TimestampMixin):
    __tablename__ = "grades"

    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id: Mapped[str] = mapped_column(String(36), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id: Mapped[str] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    grade_type_id: Mapped[str] = mapped_column(String(36), ForeignKey("grade_types.id", ondelete="RESTRICT"), nullable=False)

    value: Mapped[float] = mapped_column(Float, nullable=False)
    raw_display: Mapped[str] = mapped_column(String(20), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source: Mapped[str] = mapped_column(String(20), default=GradeSource.MANUAL.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_retake: Mapped[bool] = mapped_column(Boolean, default=False)
    original_grade_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="grades")
    lesson = relationship("Lesson", back_populates="grades")
    grade_type = relationship("GradeType", back_populates="grades")
