"""Classroom Seating Grid and Random Student Picker Router."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, require_roles
from api.services.seating_service import get_class_seating, pick_random_student, save_desk_assignment
from db.models.user import User
from db.session import get_db
from shared.enums import UserRole

router = APIRouter(prefix="/seating", tags=["Seating Chart"])


class DeskAssignPayload(BaseModel):
    row_num: int
    col_num: int
    student_id: Optional[str] = None
    desk_label: Optional[str] = None


class RandomStudentPayload(BaseModel):
    exclude_ids: Optional[List[str]] = None


@router.get("/class/{class_id}")
async def get_seating_chart(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns the visual desk arrangement and unseated students for a class."""
    return await get_class_seating(db, current_user.school_id, class_id)


@router.post("/class/{class_id}/desk")
async def update_desk_assignment(
    class_id: str,
    payload: DeskAssignPayload,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Assigns or vacates a student at a classroom desk."""
    desk = await save_desk_assignment(
        db=db,
        school_id=current_user.school_id,
        class_id=class_id,
        row_num=payload.row_num,
        col_num=payload.col_num,
        student_id=payload.student_id,
        desk_label=payload.desk_label,
    )
    return {"status": "ok", "desk_id": desk.id, "student_id": desk.student_id}


@router.post("/class/{class_id}/random")
async def select_random_student(
    class_id: str,
    payload: RandomStudentPayload,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Picks a random student fairly for recitation or answering."""
    selected = await pick_random_student(
        db=db,
        school_id=current_user.school_id,
        class_id=class_id,
        exclude_ids=payload.exclude_ids,
    )
    if not selected:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No eligible students found in class")
    return selected
