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
]
