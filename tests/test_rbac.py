"""Security and RBAC isolation tests: zero cross-user and cross-role leakage."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_student_gets_only_own_grades(client: AsyncClient, seed_data: dict):
    """A student querying their grades receives only their personal grades."""
    token = seed_data["tokens"]["student1"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/student/grades", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == seed_data["student1"].id
    assert data["overall_gpa"] == 5.0
    # Ensure student 2's grade (3.0) is not in response
    all_values = [g["value"] for sub in data["subjects"] for g in sub["grades"]]
    assert 5.0 in all_values
    assert 3.0 not in all_values


@pytest.mark.asyncio
async def test_student_cannot_query_other_student_grades(client: AsyncClient, seed_data: dict):
    """CRITICAL: A student attempting to tamper student_id parameter is rejected with 403 Forbidden."""
    token = seed_data["tokens"]["student1"]
    headers = {"Authorization": f"Bearer {token}"}
    victim_id = seed_data["student2"].id

    response = await client.get(f"/api/v1/student/grades?student_id={victim_id}", headers=headers)
    assert response.status_code == 403
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_student_forbidden_from_teacher_endpoints(client: AsyncClient, seed_data: dict):
    """Students cannot access teacher endpoints."""
    token = seed_data["tokens"]["student1"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/teacher/classes", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_student_forbidden_from_admin_endpoints(client: AsyncClient, seed_data: dict):
    """Students cannot access admin endpoints."""
    token = seed_data["tokens"]["student1"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/admin/classes", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_teacher_forbidden_from_admin_endpoints(client: AsyncClient, seed_data: dict):
    """Teachers cannot access admin endpoints."""
    token = seed_data["tokens"]["teacher"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/admin/classes", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_parent_can_access_own_child_data(client: AsyncClient, seed_data: dict):
    """Parent 1 can access verified child (Student 1) data."""
    token = seed_data["tokens"]["parent1"]
    headers = {"Authorization": f"Bearer {token}"}
    child_id = seed_data["student1"].id

    response = await client.get(f"/api/v1/parent/child/{child_id}/overview", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == child_id
    assert data["gpa"] == 5.0


@pytest.mark.asyncio
async def test_parent_forbidden_from_unrelated_child(client: AsyncClient, seed_data: dict):
    """CRITICAL: Parent 1 attempting to access Student 2 (unrelated child) is rejected with 403."""
    token = seed_data["tokens"]["parent1"]
    headers = {"Authorization": f"Bearer {token}"}
    unrelated_child_id = seed_data["student2"].id

    response = await client.get(f"/api/v1/parent/child/{unrelated_child_id}/overview", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_unauthorized_request_rejected(client: AsyncClient):
    """Requests without token must be rejected with 401."""
    response = await client.get("/api/v1/student/grades")
    assert response.status_code == 401
