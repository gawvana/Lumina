"""Tests for expiring and single-use Invite tokens."""

from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.services.invite_service import create_invite, redeem_invite
from db.models.invite import Invite
from db.models.user import User
from shared.enums import UserRole


@pytest.mark.asyncio
async def test_admin_creates_invite_token(client: AsyncClient, seed_data: dict):
    """Admin can generate an expiring invite token with deep link."""
    admin_token = seed_data["tokens"]["admin"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    payload = {
        "role": "STUDENT",
        "target_class_id": seed_data["class"].id,
        "duration_hours": 24,
        "max_uses": 1,
    }

    response = await client.post("/api/v1/admin/invites", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "deep_link" in data
    assert data["role"] == "STUDENT"
    assert data["max_uses"] == 1
    assert data["current_uses"] == 0
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_invite_redemption_and_single_use(db_session: AsyncSession, seed_data: dict):
    """An invite token can be redeemed once, and becomes inactive after max uses."""
    school = seed_data["school"]
    cls = seed_data["class"]

    # Create invite with max_uses = 1
    invite = await create_invite(
        db=db_session,
        school_id=school.id,
        role=UserRole.STUDENT.value,
        duration_hours=2,
        max_uses=1,
        target_class_id=cls.id,
    )

    # New user 1
    new_user1 = User(
        school_id=school.id,
        telegram_id=9001,
        role=UserRole.STUDENT.value,
        first_name="New",
        last_name="Student1",
    )
    db_session.add(new_user1)
    await db_session.commit()

    # First redemption -> Success
    success, err = await redeem_invite(db_session, invite.token, new_user1)
    assert success is True
    assert err is None

    # Verify invite is now inactive
    await db_session.refresh(invite)
    assert invite.current_uses == 1
    assert invite.is_active is False

    # New user 2 attempts to use same token -> Rejection
    new_user2 = User(
        school_id=school.id,
        telegram_id=9002,
        role=UserRole.STUDENT.value,
        first_name="New",
        last_name="Student2",
    )
    db_session.add(new_user2)
    await db_session.commit()

    success2, err2 = await redeem_invite(db_session, invite.token, new_user2)
    assert success2 is False
    assert err2 == "invites.already_used"


@pytest.mark.asyncio
async def test_expired_invite_token_rejected(db_session: AsyncSession, seed_data: dict):
    """Expired invite token cannot be redeemed."""
    school = seed_data["school"]

    # Create expired invite
    expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
    invite = Invite(
        school_id=school.id,
        token="expired_token_12345",
        role=UserRole.STUDENT.value,
        expires_at=expired_time,
        max_uses=1,
        current_uses=0,
        is_active=True,
    )
    db_session.add(invite)
    await db_session.commit()

    user = User(
        school_id=school.id,
        telegram_id=9003,
        role=UserRole.STUDENT.value,
        first_name="Late",
        last_name="User",
    )
    db_session.add(user)
    await db_session.commit()

    success, err = await redeem_invite(db_session, invite.token, user)
    assert success is False
    assert err == "invites.expired"
