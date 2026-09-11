"""Multi-tenant isolation and security boundary tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.academic import Class, Subject, TeacherSubjectClass
from db.models.school import School
from db.models.user import Teacher, User
from shared.config import settings
from shared.enums import UserRole
from shared.security import create_access_token


@pytest.mark.asyncio
async def test_teacher_unassigned_cannot_grade_lesson(
    client: AsyncClient, seed_data: dict, db_session: AsyncSession
):
    """
    CRITICAL: A teacher from the same school who is NOT assigned to the class/subject
    is rejected with 403 Forbidden when attempting to award a grade.
    """
    school = seed_data["school"]

    # Create an unassigned teacher
    unassigned_teacher = User(
        school_id=school.id,
        telegram_id=9999,
        role=UserRole.TEACHER.value,
        first_name="Rogue",
        last_name="Teacher",
    )
    db_session.add(unassigned_teacher)
    await db_session.flush()
    db_session.add(Teacher(id=unassigned_teacher.id, title="Substitute"))
    await db_session.commit()

    rogue_token = create_access_token(
        {"sub": unassigned_teacher.id, "role": unassigned_teacher.role, "school_id": school.id}
    )
    headers = {"Authorization": f"Bearer {rogue_token}"}

    payload = {
        "student_id": seed_data["student1"].id,
        "lesson_id": seed_data["lesson"].id,
        "grade_type_id": seed_data["grade_type_oral"].id,
        "value": 4.0,
        "raw_display": "4",
    }

    response = await client.post("/api/v1/teacher/grades", json=payload, headers=headers)
    assert response.status_code == 403
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_grade_out_of_scale_rejected(client: AsyncClient, seed_data: dict):
    """Grade values outside the school's configured grading scale (e.g. 6.0 in a 1-5 scale) are rejected."""
    teacher_token = seed_data["tokens"]["teacher"]
    headers = {"Authorization": f"Bearer {teacher_token}"}

    payload = {
        "student_id": seed_data["student1"].id,
        "lesson_id": seed_data["lesson"].id,
        "grade_type_id": seed_data["grade_type_oral"].id,
        "value": 6.0,  # Max allowed is 5.0
        "raw_display": "6",
    }

    response = await client.post("/api/v1/teacher/grades", json=payload, headers=headers)
    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_admin_cross_school_curriculum_rejected(
    client: AsyncClient, seed_data: dict, db_session: AsyncSession
):
    """
    Admin of School A cannot bind a teacher or class belonging to School B to their curriculum.
    Enforces absolute tenant isolation.
    """
    admin_token = seed_data["tokens"]["admin"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create an external School B
    foreign_school = School(name="Foreign Lyceum 2", code="FL2", settings={})
    db_session.add(foreign_school)
    await db_session.flush()

    foreign_teacher = User(
        school_id=foreign_school.id,
        telegram_id=8888,
        role=UserRole.TEACHER.value,
        first_name="Foreign",
        last_name="Instructor",
    )
    db_session.add(foreign_teacher)
    await db_session.flush()
    db_session.add(Teacher(id=foreign_teacher.id))
    await db_session.commit()

    # Admin of School A attempts to assign foreign_teacher to School A's class
    payload = {
        "teacher_id": foreign_teacher.id,
        "subject_id": seed_data["subject"].id,
        "class_id": seed_data["class"].id,
    }

    response = await client.post("/api/v1/admin/curriculum/assign", json=payload, headers=headers)
    assert response.status_code == 400
    assert "school" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_webhook_secret_token_verification(client: AsyncClient, monkeypatch):
    """Webhook requests require valid X-Telegram-Bot-Api-Secret-Token when secret is configured."""
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET", "super_secret_webhook_key_123")

    from unittest.mock import AsyncMock
    from api.routers.bot_webhook import dp
    monkeypatch.setattr(dp, "feed_update", AsyncMock(return_value=None))

    payload = {
        "update_id": 123456,
        "message": {
            "message_id": 1,
            "date": 1710000000,
            "chat": {"id": 12345, "type": "private"},
            "from": {
                "id": 12345,
                "is_bot": False,
                "first_name": "TestUser",
                "language_code": "ru",
            },
            "text": "/start",
        },
    }

    # 1. No secret header -> 403 Forbidden
    resp_no_header = await client.post("/api/v1/bot/webhook", json=payload)
    assert resp_no_header.status_code == 403

    # 2. Invalid secret header -> 403 Forbidden
    resp_bad_header = await client.post(
        "/api/v1/bot/webhook",
        json=payload,
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_secret"},
    )
    assert resp_bad_header.status_code == 403

    # 3. Valid secret header -> 200 OK
    resp_valid = await client.post(
        "/api/v1/bot/webhook",
        json=payload,
        headers={"X-Telegram-Bot-Api-Secret-Token": "super_secret_webhook_key_123"},
    )
    assert resp_valid.status_code == 200
    assert resp_valid.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_webhook_admin_endpoints_protected(client: AsyncClient, seed_data: dict):
    """Setting webhooks via /set-webhook is strictly restricted to Admin role."""
    student_token = seed_data["tokens"]["student1"]
    teacher_token = seed_data["tokens"]["teacher"]

    # Student denied
    resp1 = await client.post(
        "/api/v1/bot/set-webhook?url=https://example.com/webhook",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp1.status_code == 403

    # Teacher denied
    resp2 = await client.post(
        "/api/v1/bot/set-webhook?url=https://example.com/webhook",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert resp2.status_code == 403
