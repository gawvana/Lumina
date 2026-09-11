"""Classroom Interactive Seating Grid & Fair Random Student Picker Service."""

import random
from typing import Any, Dict, List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models.academic import Class
from db.models.seating import DeskSeating
from db.models.user import Student, User


async def get_class_seating(db: AsyncSession, school_id: str, class_id: str) -> Dict[str, Any]:
    """Returns the seating grid layout along with unassigned students in the class."""
    stmt = (
        select(DeskSeating)
        .where(DeskSeating.school_id == school_id, DeskSeating.class_id == class_id)
        .options(selectinload(DeskSeating.student).selectinload(Student.user))
        .order_by(DeskSeating.row_num.asc(), DeskSeating.col_num.asc())
    )
    desks = (await db.execute(stmt)).scalars().all()

    # Get all students in the class
    students_stmt = (
        select(Student)
        .join(User, User.id == Student.id)
        .where(Student.class_id == class_id, User.school_id == school_id, User.is_active == True)
        .options(selectinload(Student.user))
    )
    all_students = (await db.execute(students_stmt)).scalars().all()

    assigned_student_ids = {d.student_id for d in desks if d.student_id}
    unassigned = [
        {"id": s.id, "name": f"{s.user.first_name} {s.user.last_name or ''}".strip(), "xp": s.xp, "level": s.level}
        for s in all_students if s.id not in assigned_student_ids
    ]

    desk_list = []
    for d in desks:
        st_data = None
        if d.student and d.student.user:
            st_data = {
                "id": d.student.id,
                "name": f"{d.student.user.first_name} {d.student.user.last_name or ''}".strip(),
                "xp": d.student.xp,
                "level": d.student.level,
            }
        desk_list.append({
            "id": d.id,
            "row": d.row_num,
            "col": d.col_num,
            "desk_label": d.desk_label or f"{d.row_num}-{d.col_num}",
            "is_empty": d.is_empty or (d.student_id is None),
            "student": st_data,
        })

    return {
        "class_id": class_id,
        "rows": max([d["row"] for d in desk_list], default=4),
        "cols": max([d["col"] for d in desk_list], default=3),
        "desks": desk_list,
        "unassigned_students": unassigned,
    }


async def save_desk_assignment(
    db: AsyncSession,
    school_id: str,
    class_id: str,
    row_num: int,
    col_num: int,
    student_id: Optional[str] = None,
    desk_label: Optional[str] = None,
) -> DeskSeating:
    """Assigns or clears a student at a specific desk position."""
    stmt = select(DeskSeating).where(
        DeskSeating.school_id == school_id,
        DeskSeating.class_id == class_id,
        DeskSeating.row_num == row_num,
        DeskSeating.col_num == col_num,
    )
    desk = (await db.execute(stmt)).scalars().first()

    if not desk:
        desk = DeskSeating(
            school_id=school_id,
            class_id=class_id,
            row_num=row_num,
            col_num=col_num,
            desk_label=desk_label or f"{row_num}-{col_num}",
            student_id=student_id,
            is_empty=(student_id is None),
        )
        db.add(desk)
    else:
        desk.student_id = student_id
        desk.is_empty = (student_id is None)
        if desk_label:
            desk.desk_label = desk_label

    await db.commit()
    await db.refresh(desk)
    return desk


async def pick_random_student(
    db: AsyncSession,
    school_id: str,
    class_id: str,
    exclude_ids: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Fair random student selector for classroom interaction."""
    students_stmt = (
        select(Student)
        .join(User, User.id == Student.id)
        .where(Student.class_id == class_id, User.school_id == school_id, User.is_active == True)
        .options(selectinload(Student.user))
    )
    students = (await db.execute(students_stmt)).scalars().all()
    if not students:
        return None

    exclude_set = set(exclude_ids or [])
    eligible = [s for s in students if s.id not in exclude_set]
    if not eligible:
        eligible = students  # Reset pool if all excluded

    selected: Student = random.choice(eligible)
    return {
        "id": selected.id,
        "first_name": selected.user.first_name,
        "last_name": selected.user.last_name or "",
        "xp": selected.xp,
        "level": selected.level,
    }
