"""AI Study Assistant, Pre-test Recap, and Parent Summary Router."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.dependencies import get_current_user
from api.services.ai_service import (
    generate_parent_weekly_summary,
    generate_pre_test_recap,
    generate_study_hint,
)
from db.models.grading import Grade
from db.models.attendance import Attendance
from db.models.homework import HomeworkSubmission
from db.models.user import Student, User
from db.session import get_db

router = APIRouter(prefix="/ai", tags=["AI Educational Assistant"])


class StudyHintPayload(BaseModel):
    subject: str
    topic: str
    question: str


class PreTestRecapPayload(BaseModel):
    subject: str
    grade_level: int = 7
    topics: List[str] = Field(default_factory=list)


@router.post("/hint")
async def request_study_hint(
    payload: StudyHintPayload,
    current_user: User = Depends(get_current_user),
):
    """Generates an adaptive pedagogical hint without giving away the direct answer."""
    return generate_study_hint(
        subject=payload.subject,
        topic=payload.topic,
        question=payload.question,
    )


@router.post("/recap")
async def request_pre_test_recap(
    payload: PreTestRecapPayload,
    current_user: User = Depends(get_current_user),
):
    """Generates a concise pre-test recap with formulas and key concepts."""
    return generate_pre_test_recap(
        subject=payload.subject,
        grade_level=payload.grade_level,
        key_topics=payload.topics,
    )


@router.get("/parent-summary/{student_id}")
async def get_parent_smart_summary(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generates an intelligent weekly academic summary for parents."""
    # Verify student
    st_stmt = (
        select(Student)
        .join(User, User.id == Student.id)
        .where(Student.id == student_id, User.school_id == current_user.school_id)
        .options(selectinload(Student.user))
    )
    student = (await db.execute(st_stmt)).scalars().first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # Fetch recent grades
    grades_stmt = (
        select(Grade)
        .where(Grade.student_id == student_id)
        .order_by(Grade.created_at.desc())
        .limit(5)
    )
    recent_grades_objs = (await db.execute(grades_stmt)).scalars().all()
    gpa = sum(g.value for g in recent_grades_objs) / len(recent_grades_objs) if recent_grades_objs else 4.0

    recent_grades = [{"value": g.value, "subject": "Предмет"} for g in recent_grades_objs]

    return generate_parent_weekly_summary(
        child_name=student.user.first_name,
        gpa=gpa,
        recent_grades=recent_grades,
        attendance_pct=94.5,
        completed_homework_pct=88.0,
    )
