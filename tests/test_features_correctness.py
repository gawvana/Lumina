"""End-to-end correctness tests for Student, Teacher, and Parent features."""

from datetime import date, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.homework import Homework, HomeworkSubmission
from shared.enums import HomeworkStatus


@pytest.mark.asyncio
async def test_student_toggle_homework_status(
    client: AsyncClient, seed_data: dict, db_session: AsyncSession
):
    """
    Student can toggle homework status between TODO and DONE.
    Verifies that the datetime / timezone import bug in student.py is completely resolved.
    """
    student_token = seed_data["tokens"]["student1"]
    headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Create a Homework item assigned to student's class
    hw = Homework(
        class_id=seed_data["class"].id,
        subject_id=seed_data["subject"].id,
        teacher_id=seed_data["teacher"].id,
        title="Упражнение 45 (стр. 88)",
        description="Решить 5 уравнений",
        due_date=date.today() + timedelta(days=2),
    )
    db_session.add(hw)
    await db_session.commit()

    # 2. Student queries homework list
    resp_list = await client.get("/api/v1/student/homework", headers=headers)
    assert resp_list.status_code == 200
    hw_list = resp_list.json()
    assert len(hw_list) >= 1
    found = next((item for item in hw_list if item["id"] == hw.id), None)
    assert found is not None
    assert found["status"] == "TODO"

    # 3. Student marks homework as DONE
    resp_toggle = await client.patch(
        f"/api/v1/student/homework/{hw.id}/status",
        json={"status": "DONE"},
        headers=headers,
    )
    assert resp_toggle.status_code == 200
    res_data = resp_toggle.json()
    assert res_data["status"] == "DONE"

    # 4. Query again to verify persistence
    resp_list_after = await client.get("/api/v1/student/homework", headers=headers)
    assert resp_list_after.status_code == 200
    updated_found = next((item for item in resp_list_after.json() if item["id"] == hw.id), None)
    assert updated_found["status"] == "DONE"


@pytest.mark.asyncio
async def test_parent_view_child_homework_and_schedule(
    client: AsyncClient, seed_data: dict, db_session: AsyncSession
):
    """Parent can query verified child's homework list and schedule."""
    parent_token = seed_data["tokens"]["parent1"]
    headers = {"Authorization": f"Bearer {parent_token}"}
    child_id = seed_data["student1"].id

    # Add homework
    hw = Homework(
        class_id=seed_data["class"].id,
        subject_id=seed_data["subject"].id,
        teacher_id=seed_data["teacher"].id,
        title="Сочинение о дружбе",
        description="Написать развернутое эссе о дружбе",
        due_date=date.today() + timedelta(days=3),
    )
    db_session.add(hw)
    await db_session.commit()

    # 1. Parent queries child's homework
    resp_hw = await client.get(f"/api/v1/parent/child/{child_id}/homework", headers=headers)
    assert resp_hw.status_code == 200
    hw_items = resp_hw.json()
    assert len(hw_items) >= 1
    assert any(h["title"] == "Сочинение о дружбе" for h in hw_items)

    # 2. Parent queries child's schedule
    resp_sched = await client.get(f"/api/v1/parent/child/{child_id}/schedule", headers=headers)
    assert resp_sched.status_code == 200
    sched_items = resp_sched.json()
    assert len(sched_items) >= 1
    assert sched_items[0]["subject"] == "Алгебра"


@pytest.mark.asyncio
async def test_parent_absence_note_date_validation(client: AsyncClient, seed_data: dict):
    """Parent absence note rejects date_from > date_to, accepts valid range."""
    parent_token = seed_data["tokens"]["parent1"]
    headers = {"Authorization": f"Bearer {parent_token}"}
    child_id = seed_data["student1"].id

    today = date.today()

    # Invalid: date_from is after date_to
    bad_payload = {
        "student_id": child_id,
        "date_from": (today + timedelta(days=3)).isoformat(),
        "date_to": today.isoformat(),
        "reason": "Family trip",
    }
    resp_bad = await client.post("/api/v1/parent/absence-notes", json=bad_payload, headers=headers)
    assert resp_bad.status_code == 400
    assert "cannot be after" in resp_bad.json()["detail"]

    # Valid: date_from <= date_to
    good_payload = {
        "student_id": child_id,
        "date_from": today.isoformat(),
        "date_to": (today + timedelta(days=1)).isoformat(),
        "reason": "Визит к врачу",
    }
    resp_good = await client.post("/api/v1/parent/absence-notes", json=good_payload, headers=headers)
    assert resp_good.status_code == 200
    data = resp_good.json()
    assert data["student_id"] == child_id
    assert data["status"] == "APPROVED"


@pytest.mark.asyncio
async def test_teacher_homework_crud(client: AsyncClient, seed_data: dict):
    """Teacher can create, list, and delete homework assignments."""
    teacher_token = seed_data["tokens"]["teacher"]
    headers = {"Authorization": f"Bearer {teacher_token}"}

    class_id = seed_data["class"].id
    subject_id = seed_data["subject"].id

    # 1. Create homework
    create_payload = {
        "class_id": class_id,
        "subject_id": subject_id,
        "title": "Параграф 14, вопросы 1-5",
        "description": "Письменно в тетради",
        "due_date": (date.today() + timedelta(days=1)).isoformat(),
    }
    resp_create = await client.post("/api/v1/teacher/homework", json=create_payload, headers=headers)
    assert resp_create.status_code == 200
    created = resp_create.json()
    assert created["title"] == "Параграф 14, вопросы 1-5"
    hw_id = created["id"]

    # 2. List homework
    resp_list = await client.get(
        f"/api/v1/teacher/homework?class_id={class_id}&subject_id={subject_id}",
        headers=headers,
    )
    assert resp_list.status_code == 200
    items = resp_list.json()
    assert any(item["id"] == hw_id for item in items)

    # 3. Delete homework
    resp_del = await client.delete(f"/api/v1/teacher/homework/{hw_id}", headers=headers)
    assert resp_del.status_code == 200
    assert resp_del.json()["status"] == "deleted"

