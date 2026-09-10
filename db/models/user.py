"""User and role-specific profile models."""

from typing import List, Optional
from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin
from shared.enums import UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.STUDENT.value)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language_code: Mapped[str] = mapped_column(String(10), default="ru")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    school = relationship("School", back_populates="users")
    teacher_profile = relationship("Teacher", back_populates="user", uselist=False, cascade="all, delete-orphan")
    student_profile = relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")
    parent_profile = relationship("Parent", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    bio: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    user = relationship("User", back_populates="teacher_profile")
    lessons = relationship("Lesson", back_populates="teacher")
    homework = relationship("Homework", back_populates="teacher")
    teacher_subjects = relationship("TeacherSubjectClass", back_populates="teacher")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    class_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("classes.id", ondelete="SET NULL"), nullable=True, index=True)
    student_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    user = relationship("User", back_populates="student_profile")
    student_class = relationship("Class", back_populates="students")
    grades = relationship("Grade", back_populates="student")
    attendance = relationship("Attendance", back_populates="student")
    homework_submissions = relationship("HomeworkSubmission", back_populates="student")
    parent_links = relationship("StudentParent", back_populates="student", cascade="all, delete-orphan")


class Parent(Base):
    __tablename__ = "parents"

    id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Relationships
    user = relationship("User", back_populates="parent_profile")
    children_links = relationship("StudentParent", back_populates="parent", cascade="all, delete-orphan")
    absence_notes = relationship("ParentAbsenceNote", back_populates="parent")


class StudentParent(Base, TimestampMixin):
    __tablename__ = "student_parents"
    __table_args__ = (
        UniqueConstraint("student_id", "parent_id", name="uq_student_parent"),
    )

    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id: Mapped[str] = mapped_column(String(36), ForeignKey("parents.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(50), default="guardian")
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    student = relationship("Student", back_populates="parent_links")
    parent = relationship("Parent", back_populates="children_links")
