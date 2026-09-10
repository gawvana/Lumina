"""Academic structure models: Classes, Subjects, Curriculum links, Lessons."""

from datetime import date
from typing import Optional
from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin
from shared.enums import LessonStatus


class Class(Base, TimestampMixin):
    __tablename__ = "classes"

    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relationships
    school = relationship("School", back_populates="classes")
    students = relationship("Student", back_populates="student_class")
    lessons = relationship("Lesson", back_populates="class_rel")
    homework = relationship("Homework", back_populates="class_rel")
    curriculum_links = relationship("TeacherSubjectClass", back_populates="class_rel")


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"

    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False)

    # Relationships
    school = relationship("School", back_populates="subjects")
    lessons = relationship("Lesson", back_populates="subject")
    homework = relationship("Homework", back_populates="subject")
    curriculum_links = relationship("TeacherSubjectClass", back_populates="subject")


class TeacherSubjectClass(Base, TimestampMixin):
    """Maps which Teacher teaches which Subject in which Class."""
    __tablename__ = "teacher_subject_classes"
    __table_args__ = (
        UniqueConstraint("teacher_id", "subject_id", "class_id", name="uq_teacher_subject_class"),
    )

    teacher_id: Mapped[str] = mapped_column(String(36), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id: Mapped[str] = mapped_column(String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationships
    teacher = relationship("Teacher", back_populates="teacher_subjects")
    subject = relationship("Subject", back_populates="curriculum_links")
    class_rel = relationship("Class", back_populates="curriculum_links")


class Lesson(Base, TimestampMixin):
    __tablename__ = "lessons"

    class_id: Mapped[str] = mapped_column(String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id: Mapped[str] = mapped_column(String(36), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_number: Mapped[int] = mapped_column(Integer, nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    room: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=LessonStatus.SCHEDULED.value)

    # Relationships
    class_rel = relationship("Class", back_populates="lessons")
    subject = relationship("Subject", back_populates="lessons")
    teacher = relationship("Teacher", back_populates="lessons")
    grades = relationship("Grade", back_populates="lesson")
    attendance = relationship("Attendance", back_populates="lesson")
    homework = relationship("Homework", back_populates="lesson")
