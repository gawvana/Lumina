"""Tests for Grade awarding, correction, and AuditLog integrity."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.audit import AuditLog
from db.models.grading import Grade
from shared.enums import AuditAction, AuditEntityType


@pytest.mark.asyncio
async def test_grade_creation_records_audit(client: AsyncClient, seed_data: dict, db_session: AsyncSession):
    """Awarding a grade creates both the Grade entry and an immutable AuditLog record."""
    teacher_token = seed_data["tokens"]["teacher"]
    headers = {"Authorization": f"Bearer {teacher_token}"}

    payload = {
        "student_id": seed_data["student1"].id,
        "lesson_id": seed_data["lesson"].id,
        "grade_type_id": seed_data["grade_type_oral"].id,
        "value": 4.0,
        "raw_display": "4",
        "comment": "Хороший ответ",
        "weight": 1.0,
    }

    response = await client.post("/api/v1/teacher/grades", json=payload, headers=headers)
    assert response.status_code == 200
    grade_data = response.json()
    assert grade_data["value"] == 4.0

    # Verify Audit Log entry created in database
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.entity_type == AuditEntityType.GRADE.value,
            AuditLog.entity_id == grade_data["id"],
            AuditLog.action == AuditAction.CREATE.value,
        )
    )
    result = await db_session.execute(stmt)
    audit = result.scalars().first()
    assert audit is not None
    assert audit.user_id == seed_data["teacher"].id
    assert audit.new_values["value"] == 4.0


@pytest.mark.asyncio
async def test_grade_correction_preserves_history(client: AsyncClient, seed_data: dict, db_session: AsyncSession):
    """Editing a grade modifies current value while recording old and new states in AuditLog."""
    teacher_token = seed_data["tokens"]["teacher"]
    headers = {"Authorization": f"Bearer {teacher_token}"}
    grade_id = seed_data["grade1"].id  # Originally 5.0

    update_payload = {
        "value": 4.0,
        "raw_display": "4",
        "comment": "Уточнённая оценка",
        "is_retake": True,
        "reason": "Перепроверка работы",
    }

    response = await client.patch(f"/api/v1/teacher/grades/{grade_id}", json=update_payload, headers=headers)
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["value"] == 4.0
    assert updated_data["is_retake"] is True

    # Verify Audit Log captures old and new values
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.entity_type == AuditEntityType.GRADE.value,
            AuditLog.entity_id == grade_id,
            AuditLog.action == AuditAction.UPDATE.value,
        )
    )
    result = await db_session.execute(stmt)
    audit = result.scalars().first()
    assert audit is not None
    assert audit.old_values["value"] == 5.0
    assert audit.new_values["value"] == 4.0
    assert audit.new_values["is_retake"] is True
