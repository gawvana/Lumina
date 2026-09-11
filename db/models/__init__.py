"""Database models package."""

from db.models.base import Base, TimestampMixin
from db.models.school import School
from db.models.feature_flag import FeatureFlag
from db.models.user import User, Teacher, Student, Parent, StudentParent
from db.models.academic import Class, Subject, TeacherSubjectClass, Lesson
from db.models.grading import GradingSystem, GradeType, Grade
from db.models.attendance import Attendance, ParentAbsenceNote
from db.models.homework import Homework, HomeworkSubmission
from db.models.invite import Invite
from db.models.audit import AuditLog
from db.models.gamification import (
    XPTransaction,
    Streak,
    Achievement,
    UserAchievement,
    VibeEntry,
    TeacherPrivateNote,
)
from db.models.seating import DeskSeating
from db.models.study import FlashcardSet, FlashcardItem, SkillNode, StudentSkill
from db.models.file import DigitalBackpackFile

__all__ = [
    "Base",
    "TimestampMixin",
    "School",
    "FeatureFlag",
    "User",
    "Teacher",
    "Student",
    "Parent",
    "StudentParent",
    "Class",
    "Subject",
    "TeacherSubjectClass",
    "Lesson",
    "GradingSystem",
    "GradeType",
    "Grade",
    "Attendance",
    "ParentAbsenceNote",
    "Homework",
    "HomeworkSubmission",
    "Invite",
    "AuditLog",
    "XPTransaction",
    "Streak",
    "Achievement",
    "UserAchievement",
    "VibeEntry",
    "TeacherPrivateNote",
    "DeskSeating",
    "FlashcardSet",
    "FlashcardItem",
    "SkillNode",
    "StudentSkill",
    "DigitalBackpackFile",
]
