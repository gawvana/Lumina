"""Tests for Seating Chart, Quick-Grading with Undo, and AI Study Assistant."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_quick_grade_and_undo_flow(
    client: AsyncClient, seed_data: dict, db_session: AsyncSession
):
    teacher_token = seed_data["tokens"]["teacher"]
    student_id = seed_data["student1"].id
    lesson_id = seed_data["lesson"].id
    headers = {"Authorization": f"Bearer {teacher_token}"}

    # 1. Quick grade student
    payload = {
        "student_id": student_id,
        "lesson_id": lesson_id,
        "value": 5.0,
        "grade_type": "classwork",
        "comment": "Отличный ответ у доски",
        "tag": "EXCELLENT",
    }
    resp = await client.post("/api/v1/teacher/quick-grade", json=payload, headers=headers)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["value"] == 5.0
    assert res_data["xp_awarded"] == 20
    assert res_data["undo_available"] is True
    grade_id = res_data["id"]

    # 2. Undo the grade within 5 minutes
    undo_resp = await client.post(f"/api/v1/teacher/undo-grade/{grade_id}", headers=headers)
    assert undo_resp.status_code == 200
    undo_data = undo_resp.json()
    assert undo_data["status"] == "undone"
    assert undo_data["grade_id"] == grade_id

    # 3. Trying to undo again returns 404 (since grade was removed)
    undo_again = await client.post(f"/api/v1/teacher/undo-grade/{grade_id}", headers=headers)
    assert undo_again.status_code in [400, 404]


@pytest.mark.asyncio
async def test_seating_chart_and_random_student(
    client: AsyncClient, seed_data: dict, db_session: AsyncSession
):
    teacher_token = seed_data["tokens"]["teacher"]
    class_id = seed_data["class"].id
    student_id = seed_data["student1"].id
    headers = {"Authorization": f"Bearer {teacher_token}"}

    # 1. Assign student to row 1, col 1
    assign_payload = {
        "row_num": 1,
        "col_num": 1,
        "student_id": student_id,
        "desk_label": "Desk 1-1",
    }
    resp_assign = await client.post(f"/api/v1/seating/class/{class_id}/desk", json=assign_payload, headers=headers)
    assert resp_assign.status_code == 200
    assert resp_assign.json()["status"] == "ok"

    # 2. Get seating grid
    resp_grid = await client.get(f"/api/v1/seating/class/{class_id}", headers=headers)
    assert resp_grid.status_code == 200
    grid_data = resp_grid.json()
    assert len(grid_data["desks"]) >= 1
    found_desk = next((d for d in grid_data["desks"] if d["student"] and d["student"]["id"] == student_id), None)
    assert found_desk is not None

    # 3. Pick random student
    random_resp = await client.post(f"/api/v1/seating/class/{class_id}/random", json={}, headers=headers)
    assert random_resp.status_code == 200
    selected = random_resp.json()
    assert selected["id"] in [seed_data["student1"].id, seed_data["student2"].id]


@pytest.mark.asyncio
async def test_ai_study_assistant_fallback(
    client: AsyncClient, seed_data: dict, db_session: AsyncSession
):
    student_token = seed_data["tokens"]["student1"]
    headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Ask for an AI study hint
    hint_payload = {
        "subject": "Алгебра",
        "topic": "Квадратные уравнения",
        "question": "Как найти дискриминант?",
    }
    hint_resp = await client.post("/api/v1/ai/hint", json=hint_payload, headers=headers)
    assert hint_resp.status_code == 200
    hint_data = hint_resp.json()
    assert "hint" in hint_data
    assert "thought_question" in hint_data
    assert len(hint_data["hint"]) > 0

    # 2. Request pre-test recap
    recap_payload = {
        "subject": "Физика",
        "grade_level": 8,
        "topics": ["Законы Ньютона", "Гравитация"],
    }
    recap_resp = await client.post("/api/v1/ai/recap", json=recap_payload, headers=headers)
    assert recap_resp.status_code == 200
    recap_data = recap_resp.json()
    assert "sections" in recap_data
    assert len(recap_data["sections"]) >= 1
