"""Pytest fixtures for async database, mock entities, and HTTP client."""

import asyncio
import hashlib
import hmac
import time
from datetime import date, datetime, timedelta, timezone
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.main import app
from db.models.academic import Class, Lesson, Subject, TeacherSubjectClass
from db.models.base import Base
from db.models.feature_flag import FeatureFlag
from db.models.grading import Grade, GradeType, GradingSystem
from db.models.school import School
from db.models.user import Parent, Student, StudentParent, Teacher, User
from db.session import get_db
from shared.enums import GradingSystemType, UserRole
from shared.security import create_access_token

TEST_BOT_TOKEN = "123456789:ABCdefGhIJKlmNoPQRstuVWXyz_TestBotToken"
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)
TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Creates a fresh in-memory database per test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provides an AsyncClient hooked to the test DB."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


def generate_test_init_data(
    user_id: int,
    first_name: str = "TestUser",
    last_name: str = "Testov",
    username: str = "testuser",
    bot_token: str = TEST_BOT_TOKEN,
    auth_date: int = None,
    tampered: bool = False,
) -> str:
    """Generates valid Telegram WebApp initData string."""
    if auth_date is None:
        auth_date = int(time.time())

    user_json = f'{{"id":{user_id},"first_name":"{first_name}","last_name":"{last_name}","username":"{username}","language_code":"ru"}}'
    data_dict = {
        "auth_date": str(auth_date),
        "query_id": "AAHdF6IQAAAAAN0XohDhrP_Y",
        "user": user_json,
    }

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data_dict.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if tampered:
        calc_hash = "deadbeef" + calc_hash[8:]

    from urllib.parse import quote
    return f"auth_date={auth_date}&query_id=AAHdF6IQAAAAAN0XohDhrP_Y&user={quote(user_json)}&hash={calc_hash}"


@pytest_asyncio.fixture
async def seed_data(db_session: AsyncSession):
    """Seeds a realistic school environment for testing."""
    # School 1
    school = School(name="Test Gymnasium 1", code="TG1", settings={})
    db_session.add(school)
    await db_session.flush()

    for flag in FeatureFlag.get_default_flags(school.id):
        db_session.add(flag)

    gs = GradingSystem(
        school_id=school.id,
        name="5-балльная система",
        system_type=GradingSystemType.POINTS_5.value,
        config={"min": 1, "max": 5},
    )
    db_session.add(gs)

    # Grade Types
    gt_oral = GradeType(school_id=school.id, name="Ответ у доски", code="oral", weight=1.0)
    gt_test = GradeType(school_id=school.id, name="Контрольная", code="test", weight=2.0)
    db_session.add_all([gt_oral, gt_test])
    await db_session.flush()

    # Admin User
    admin = User(
        school_id=school.id,
        telegram_id=1001,
        role=UserRole.ADMIN.value,
        first_name="Admin",
        last_name="Director",
    )
    db_session.add(admin)

    # Teacher User
    teacher = User(
        school_id=school.id,
        telegram_id=1002,
        role=UserRole.TEACHER.value,
        first_name="Elena",
        last_name="Ivanova",
    )
    db_session.add(teacher)
    await db_session.flush()
    teacher_prof = Teacher(id=teacher.id, title="Math Teacher")
    db_session.add(teacher_prof)

    # Class & Subject
    cls = Class(school_id=school.id, name="7-A", grade_level=7, academic_year="2026-2027")
    sub = Subject(school_id=school.id, name="Алгебра", code="ALG")
    db_session.add_all([cls, sub])
    await db_session.flush()

    tsc = TeacherSubjectClass(teacher_id=teacher.id, subject_id=sub.id, class_id=cls.id)
    db_session.add(tsc)

    # Students 1 and 2
    student1 = User(
        school_id=school.id,
        telegram_id=2001,
        role=UserRole.STUDENT.value,
        first_name="Alisher",
        last_name="Usmanov",
    )
    student2 = User(
        school_id=school.id,
        telegram_id=2002,
        role=UserRole.STUDENT.value,
        first_name="Timur",
        last_name="Bekov",
    )
    db_session.add_all([student1, student2])
    await db_session.flush()

    sp1 = Student(id=student1.id, class_id=cls.id, student_number="01")
    sp2 = Student(id=student2.id, class_id=cls.id, student_number="02")
    db_session.add_all([sp1, sp2])

    # Parent 1 (Parent of Student 1 only)
    parent1 = User(
        school_id=school.id,
        telegram_id=3001,
        role=UserRole.PARENT.value,
        first_name="Nodira",
        last_name="Usmanova",
    )
    db_session.add(parent1)
    await db_session.flush()
    pp1 = Parent(id=parent1.id)
    db_session.add(pp1)
    sp_link = StudentParent(student_id=student1.id, parent_id=parent1.id, relationship_type="mother")
    db_session.add(sp_link)

    # Lesson
    today = date.today()
    lesson = Lesson(
        class_id=cls.id,
        subject_id=sub.id,
        teacher_id=teacher.id,
        lesson_date=today,
        period_number=1,
        topic="Квадратные уравнения",
        room="101",
    )
    db_session.add(lesson)
    await db_session.flush()

    # Grade for student 1
    grade1 = Grade(
        school_id=school.id,
        student_id=student1.id,
        teacher_id=teacher.id,
        lesson_id=lesson.id,
        subject_id=sub.id,
        grade_type_id=gt_oral.id,
        value=5.0,
        raw_display="5",
        comment="Молодец!",
    )
    db_session.add(grade1)

    # Grade for student 2
    grade2 = Grade(
        school_id=school.id,
        student_id=student2.id,
        teacher_id=teacher.id,
        lesson_id=lesson.id,
        subject_id=sub.id,
        grade_type_id=gt_test.id,
        value=3.0,
        raw_display="3",
        comment="Нужно повторить формулы",
    )
    db_session.add(grade2)

    await db_session.commit()

    return {
        "school": school,
        "admin": admin,
        "teacher": teacher,
        "student1": student1,
        "student2": student2,
        "parent1": parent1,
        "class": cls,
        "subject": sub,
        "lesson": lesson,
        "grade_type_oral": gt_oral,
        "grade_type_test": gt_test,
        "grade1": grade1,
        "grade2": grade2,
        "tokens": {
            "admin": create_access_token({"sub": admin.id, "role": admin.role, "school_id": school.id}),
            "teacher": create_access_token({"sub": teacher.id, "role": teacher.role, "school_id": school.id}),
            "student1": create_access_token({"sub": student1.id, "role": student1.role, "school_id": school.id}),
            "student2": create_access_token({"sub": student2.id, "role": student2.role, "school_id": school.id}),
            "parent1": create_access_token({"sub": parent1.id, "role": parent1.role, "school_id": school.id}),
        },
    }
