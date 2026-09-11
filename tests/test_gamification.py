"""Tests for Gamification: XP, Levels, Streaks, Achievements, and Vibe Check."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.xp_service import award_xp


@pytest.mark.asyncio
async def test_gamification_profile_and_xp_service(
    client: AsyncClient, seed_data: dict, db_session: AsyncSession
):
    student_token = seed_data["tokens"]["student1"]
    student_id = seed_data["student1"].id
    school_id = seed_data["school"].id
    headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Query gamification profile
    resp = await client.get("/api/v1/gamification/profile", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "xp" in data
    assert "level" in data
    assert "streak_days" in data
    assert "achievements" in data
    assert data["xp"] == 0
    assert data["level"] == 1

    # 2. Award XP via award_xp service
    awarded_data = await award_xp(
        db=db_session,
        school_id=school_id,
        student_id=student_id,
        amount=250,
        reason="Completed math homework on time",
        source="homework",
    )
    assert awarded_data["amount"] == 250
    assert awarded_data["level"] == 2

    # 3. Query profile again to verify total_xp and level calculation
    resp2 = await client.get("/api/v1/gamification/profile", headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["xp"] == 250
    assert data2["level"] == 2


@pytest.mark.asyncio
async def test_student_vibe_check(
    client: AsyncClient, seed_data: dict, db_session: AsyncSession
):
    student_token = seed_data["tokens"]["student1"]
    headers = {"Authorization": f"Bearer {student_token}"}

    # Submit a vibe
    payload = {
        "vibe_type": "energized",
        "note": "Ready for calculus!",
        "is_private": True,
    }
    resp = await client.post("/api/v1/gamification/vibe", json=payload, headers=headers)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["status"] == "ok"
    assert res_data["vibe"] == "energized"
