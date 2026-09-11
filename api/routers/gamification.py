"""Gamification Router: XP, Level, Streaks, Achievements, and Vibe Check."""

from datetime import date
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user
from api.services.xp_service import (
    get_student_gamification_profile,
    record_daily_activity,
)
from db.models.gamification import VibeEntry
from db.models.user import Student, User
from db.session import get_db

router = APIRouter(prefix="/gamification", tags=["Gamification"])


class VibePayload(BaseModel):
    vibe_type: str = Field(..., description="energized, focused, neutral, tired, stressed")
    note: Optional[str] = None
    is_private: bool = True


@router.get("/profile")
async def get_my_gamification_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns XP, Level, Daily Streak, Achievements, and today's Vibe."""
    student_id = current_user.id
    # Automatically track daily activity streak
    await record_daily_activity(db, student_id)
    return await get_student_gamification_profile(db, student_id)


@router.post("/vibe")
async def set_student_daily_vibe(
    payload: VibePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Records or updates student's daily vibe check."""
    student_id = current_user.id
    today = date.today()

    stmt = select(VibeEntry).where(VibeEntry.student_id == student_id, VibeEntry.entry_date == today)
    existing = (await db.execute(stmt)).scalars().first()

    if existing:
        existing.vibe_type = payload.vibe_type
        existing.note = payload.note
        existing.is_private = payload.is_private
    else:
        entry = VibeEntry(
            student_id=student_id,
            vibe_type=payload.vibe_type,
            note=payload.note,
            entry_date=today,
            is_private=payload.is_private,
        )
        db.add(entry)

    await db.commit()
    return {"status": "ok", "vibe": payload.vibe_type, "date": today.isoformat()}
