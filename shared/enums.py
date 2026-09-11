"""Shared enums for Lumina - Telegram School OS."""

from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"
    PARENT = "PARENT"


class GradeSource(str, Enum):
    MANUAL = "MANUAL"
    VOICE = "VOICE"


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"


class HomeworkStatus(str, Enum):
    TODO = "TODO"
    DONE = "DONE"
    OVERDUE = "OVERDUE"


class LessonStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REPLACED = "REPLACED"


class GradingSystemType(str, Enum):
    POINTS_5 = "POINTS_5"
    POINTS_10 = "POINTS_10"
    POINTS_12 = "POINTS_12"
    POINTS_100 = "POINTS_100"
    LETTER = "LETTER"


class AuditAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class AuditEntityType(str, Enum):
    GRADE = "GRADE"
    ATTENDANCE = "ATTENDANCE"
    USER = "USER"
    INVITE = "INVITE"
    CLASS = "CLASS"
    SUBJECT = "SUBJECT"
    FEATURE_FLAG = "FEATURE_FLAG"
    HOMEWORK = "HOMEWORK"


class AbsenceNoteStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class FeatureFlagName(str, Enum):
    VOICE_GRADING = "voice_grading"
    VIBE_TRACKING = "vibe_tracking"
    SKINS = "skins"
    LEADERBOARD = "leaderboard"
    FLASHCARDS = "flashcards"
    STUDENT_REACTIONS = "student_reactions"
    AI_FEATURES = "ai_features"
    SECOND_CHANCE = "second_chance"
    VIDEO_CIRCLES = "video_circles"
    SECRET_COMMANDS = "secret_commands"
