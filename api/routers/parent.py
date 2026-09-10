"""Parent router: children monitoring, grades, attendance, homework, and absence notes.
Strictly verifies that a parent can ONLY access verified linked children.
"""

from datetime import date
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.dependencies import require_roles
from api.schemas.journal import AbsenceNoteCreateRequest
from db.models.academic import Lesson
from db.models.attendance import Attendance, ParentAbsenceNote
from db.models.grading import Grade
from db.models.homework import Homework
from db.models.user import Student, StudentParent, User
from db.session import get_db
from shared.enums import AbsenceNoteStatus, AttendanceStatus, UserRole
from shared.i18n import t

router = APIRouter(
    prefix="/parent",
    tags=["Parent"],
    dependencies=[Depends(require_roles(UserRole.PARENT, UserRole.ADMIN))],
)


async def verify_child_access(parent_id: str, student_id: str, db: AsyncSession) -> Student:
    """Verifies that the parent is actively linked to the student; raises 403 otherwise."""
    stmt = select(StudentParent).where(
        StudentParent.parent_id == parent_id,
        StudentParent.student_id == student_id,
        StudentParent.is_confirmed == True,
    )
    res = await db.execute(stmt)
    link = res.scalars().first()
    if not link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=t("errors.access_denied"),
        )

    student = await db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail=t("errors.not_found"))
    return student


@router.get("/children")
async def get_parent_children(
    current_user: User = Depends(require_roles(UserRole.PARENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Returns list of children linked to the parent."""
    stmt = (
        select(StudentParent)
        .where(StudentParent.parent_id == current_user.id, StudentParent.is_confirmed == True)
        .options(
            selectinload(StudentParent.student).selectinload(Student.user),
            selectinload(StudentParent.student).selectinload(Student.student_class),
        )
    )
    res = await db.execute(stmt)
    links = res.scalars().all()

    return [
        {
            "student_id": link.student.id,
            "name": f"{link.student.user.first_name} {link.student.user.last_name or ''}".strip(),
            "class_name": link.student.student_class.name if link.student.student_class else "",
            "relationship": link.relationship_type,
        }
        for link in links
        if link.student and link.student.user
    ]


@router.get("/child/{student_id}/overview")
async def get_child_overview(
    student_id: str,
    current_user: User = Depends(require_roles(UserRole.PARENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Returns child summary, strictly checking parent link."""
    if current_user.role != UserRole.ADMIN.value:
        await verify_child_access(current_user.id, student_id, db)

    # Latest grades
    g_stmt = (
        select(Grade)
        .where(Grade.student_id == student_id, Grade.is_active == True)
        .options(selectinload(Grade.grade_type), selectinload(Grade.lesson).selectinload(Lesson.subject))
        .order_by(Grade.created_at.desc())
        .limit(5)
    )
    g_res = await db.execute(g_stmt)
    recent_grades = g_res.scalars().all()

    all_grades_stmt = select(Grade.value).where(Grade.student_id == student_id, Grade.is_active == True)
    all_g_res = await db.execute(all_grades_stmt)
    all_vals = all_g_res.scalars().all()
    gpa = round(sum(all_vals) / len(all_vals), 2) if all_vals else 0.0

    return {
        "student_id": student_id,
        "gpa": gpa,
        "recent_grades": [
            {
                "subject": g.lesson.subject.name if (g.lesson and g.lesson.subject) else "",
                "value": g.value,
                "raw_display": g.raw_display,
                "type": g.grade_type.name if g.grade_type else "",
                "date": g.created_at.date().isoformat(),
            }
            for g in recent_grades
        ],
    }


@router.get("/child/{student_id}/grades")
async def get_child_grades(
    student_id: str,
    current_user: User = Depends(require_roles(UserRole.PARENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Returns child's grades grouped by subject."""
    if current_user.role != UserRole.ADMIN.value:
        await verify_child_access(current_user.id, student_id, db)

    stmt = (
        select(Grade)
        .where(Grade.student_id == student_id, Grade.is_active == True)
        .options(selectinload(Grade.grade_type), selectinload(Grade.lesson).selectinload(Lesson.subject))
        .order_by(Grade.created_at.desc())
    )
    res = await db.execute(stmt)
    grades = res.scalars().all()

    return [
        {
            "id": g.id,
            "subject": g.lesson.subject.name if (g.lesson and g.lesson.subject) else "",
            "value": g.value,
            "raw_display": g.raw_display,
            "comment": g.comment,
            "type": g.grade_type.name if g.grade_type else "",
            "date": g.created_at.date().isoformat(),
        }
        for g in grades
    ]


@router.get("/child/{student_id}/attendance")
async def get_child_attendance(
    student_id: str,
    current_user: User = Depends(require_roles(UserRole.PARENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Returns child's attendance record."""
    if current_user.role != UserRole.ADMIN.value:
        await verify_child_access(current_user.id, student_id, db)

    stmt = (
        select(Attendance)
        .where(Attendance.student_id == student_id)
        .options(selectinload(Attendance.lesson).selectinload(Lesson.subject))
        .order_by(Attendance.recorded_at.desc())
    )
    res = await db.execute(stmt)
    records = res.scalars().all()

    return [
        {
            "id": a.id,
            "date": a.lesson.lesson_date.isoformat() if a.lesson else "",
            "subject": a.lesson.subject.name if (a.lesson and a.lesson.subject) else "",
            "status": a.status,
            "note": a.note,
        }
        for a in records
    ]


@router.post("/absence-notes")
async def submit_digital_absence_note(
    payload: AbsenceNoteCreateRequest,
    current_user: User = Depends(require_roles(UserRole.PARENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits a digital absence note for a child.
    Automatically marks existing/future lessons in date range as EXCUSED in the journal!
    """
    if current_user.role != UserRole.ADMIN.value:
        await verify_child_access(current_user.id, payload.student_id, db)

    note = ParentAbsenceNote(
        student_id=payload.student_id,
        parent_id=current_user.id,
        date_from=payload.date_from,
        date_to=payload.date_to,
        reason=payload.reason,
        status=AbsenceNoteStatus.APPROVED.value,
    )
    db.add(note)
    await db.flush()

    # Find student's lessons in date range
    student = await db.get(Student, payload.student_id)
    if student and student.class_id:
        lessons_stmt = select(Lesson).where(
            Lesson.class_id == student.class_id,
            Lesson.lesson_date >= payload.date_from,
            Lesson.lesson_date <= payload.date_to,
        )
        l_res = await db.execute(lessons_stmt)
        lessons = l_res.scalars().all()

        for lesson in lessons:
            att_stmt = select(Attendance).where(
                Attendance.student_id == payload.student_id,
                Attendance.lesson_id == lesson.id,
            )
            att_res = await db.execute(att_stmt)
            record = att_res.scalars().first()

            if record:
                record.status = AttendanceStatus.EXCUSED.value
                record.note = f"Записка: {payload.reason}"
                record.parent_note_id = note.id
            else:
                record = Attendance(
                    student_id=payload.student_id,
                    lesson_id=lesson.id,
                    status=AttendanceStatus.EXCUSED.value,
                    note=f"Записка: {payload.reason}",
                    parent_note_id=note.id,
                    recorded_by_id=current_user.id,
                )
                db.add(record)

    await db.commit()
    await db.refresh(note)
    return note
