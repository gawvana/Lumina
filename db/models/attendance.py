"""Attendance and Parent Absence Notes models."""

from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin
from shared.enums import AbsenceNoteStatus, AttendanceStatus


class Attendance(Base, TimestampMixin):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("student_id", "lesson_id", name="uq_student_lesson_attendance"),
    )

    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id: Mapped[str] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default=AttendanceStatus.PRESENT.value)
    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    parent_note_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("parent_absence_notes.id", ondelete="SET NULL"), nullable=True)
    recorded_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    student = relationship("Student", back_populates="attendance")
    lesson = relationship("Lesson", back_populates="attendance")
    parent_note = relationship("ParentAbsenceNote", back_populates="attendance_records")


class ParentAbsenceNote(Base, TimestampMixin):
    __tablename__ = "parent_absence_notes"

    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id: Mapped[str] = mapped_column(String(36), ForeignKey("parents.id", ondelete="CASCADE"), nullable=False, index=True)
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=AbsenceNoteStatus.PENDING.value)

    # Relationships
    parent = relationship("Parent", back_populates="absence_notes")
    attendance_records = relationship("Attendance", back_populates="parent_note")
