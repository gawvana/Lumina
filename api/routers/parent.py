"""Parent router: children monitoring, grades, attendance, homework, schedule, and absence notes.
Strictly verifies that a parent can ONLY access verified linked children in the same school.
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.dependencies import require_roles
from api.schemas.journal import AbsenceNoteCreateRequest
from api.services.audit_service import record_audit
from db.models.academic import Lesson
from db.models.attendance import Attendance, ParentAbsenceNote
from db.models.grading import Grade
from db.models.homework import Homework, HomeworkSubmission
from db.models.user import Student, StudentParent, User
from db.session import get_db
from shared.enums import AbsenceNoteStatus, AttendanceStatus, AuditAction, AuditEntityType, HomeworkStatus, UserRole
from shared.i18n import t

router = APIRouter(
    prefix="/parent",
    tags=["Parent"],
    dependencies=[Depends(require_roles(UserRole.PARENT, UserRole.ADMIN))],
)


async def verify_child_access(parent_id: str, student_id: str, school_id: str, db: AsyncSession) -> Student:
    """Verifies that the parent is actively linked to the student in the same school; raises 403 otherwise."""
    stmt = (
        select(StudentParent)
        .join(Student, StudentParent.student_id == Student.id)
        .join(User, Student.id == User.id)
        .where(
            StudentParent.parent_id == parent_id,
            StudentParent.student_id == student_id,
            StudentParent.is_confirmed == True,
            User.school_id == school_id,
        )
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
            "class_id": link.student.class_id or "",
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
        await verify_child_access(current_user.id, student_id, current_user.school_id, db)

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
        await verify_child_access(current_user.id, student_id, current_user.school_id, db)

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
    """Returns child's attendance records."""
    if current_user.role != UserRole.ADMIN.value:
        await verify_child_access(current_user.id, student_id, current_user.school_id, db)

    stmt = (
        select(Attendance)
        .where(Attendance.student_id == student_id)
        .options(selectinload(Attendance.lesson).selectinload(Lesson.subject))
        .order_by(Attendance.recorded_at.desc())
        .limit(50)
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


@router.get("/child/{student_id}/homework")
async def get_child_homework(
    student_id: str,
    current_user: User = Depends(require_roles(UserRole.PARENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Returns child's homework list and completion status."""
    student = await verify_child_access(current_user.id, student_id, current_user.school_id, db) if current_user.role != UserRole.ADMIN.value else await db.get(Student, student_id)
    if not student or not student.class_id:
        return []

    stmt = (
        select(Homework)
        .where(Homework.class_id == student.class_id)
        .options(selectinload(Homework.subject))
        .order_by(Homework.due_date.desc())
        .limit(30)
    )
    res = await db.execute(stmt)
    homework_list = res.scalars().all()

    # Get child's submissions
    sub_stmt = select(HomeworkSubmission).where(HomeworkSubmission.student_id == student_id)
    sub_res = await db.execute(sub_stmt)
    submissions = {s.homework_id: s.status for s in sub_res.scalars().all()}

    today = date.today()
    result = []
    for hw in homework_list:
        sub_status = submissions.get(hw.id, HomeworkStatus.TODO.value)
        if sub_status == HomeworkStatus.TODO.value and hw.due_date < today:
            sub_status = HomeworkStatus.OVERDUE.value

        result.append({
            "id": hw.id,
            "title": hw.title,
            "description": hw.description,
            "due_date": hw.due_date.isoformat(),
            "subject": hw.subject.name if hw.subject else "",
            "status": sub_status,
        })

    return result


@router.get("/child/{student_id}/schedule")
async def get_child_schedule(
    student_id: str,
    current_user: User = Depends(require_roles(UserRole.PARENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Returns timetable for child's class."""
    student = await verify_child_access(current_user.id, student_id, current_user.school_id, db) if current_user.role != UserRole.ADMIN.value else await db.get(Student, student_id)
    if not student or not student.class_id:
        return []

    stmt = (
        select(Lesson)
        .where(Lesson.class_id == student.class_id)
        .options(selectinload(Lesson.subject))
        .order_by(Lesson.lesson_date, Lesson.period_number)
        .limit(60)
    )
    res = await db.execute(stmt)
    lessons = res.scalars().all()

    return [
        {
            "id": l.id,
            "date": l.lesson_date.isoformat(),
            "period": l.period_number,
            "subject": l.subject.name if l.subject else "",
            "room": l.room or "",
            "status": l.status,
        }
        for l in lessons
    ]


@router.post("/absence-notes")
async def submit_digital_absence_note(
    payload: AbsenceNoteCreateRequest,
    current_user: User = Depends(require_roles(UserRole.PARENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits a digital absence note for a child.
    Validates dates, creates note, auto-excuses lessons in date range, and logs audit.
    """
    if payload.date_from > payload.date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date (date_from) cannot be after end date (date_to)",
        )

    if current_user.role != UserRole.ADMIN.value:
        await verify_child_access(current_user.id, payload.student_id, current_user.school_id, db)

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

    # Find student's lessons in date range and mark excused
    student = await db.get(Student, payload.student_id)
    excused_count = 0
    if student and student.class_id:
        lessons_stmt = select(Lesson).where(
            Lesson.class_id == student.class_id,
            Lesson.lesson_date >= payload.date_from,
            Lesson.lesson_date <= payload.date_to,
        )
        l_res = await db.execute(lessons_stmt)
        lessons = l_res.scalars().all()

        now_utc = datetime.now(timezone.utc)
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
                    recorded_at=now_utc,
                )
                db.add(record)
            excused_count += 1

    # Record Audit Log
    await record_audit(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        entity_type=AuditEntityType.ATTENDANCE.value,
        entity_id=note.id,
        action=AuditAction.CREATE.value,
        new_values={
            "student_id": payload.student_id,
            "date_from": payload.date_from.isoformat(),
            "date_to": payload.date_to.isoformat(),
            "excused_lessons_count": excused_count,
        },
        reason=f"Digital absence note submitted: {payload.reason}",
    )

    await db.commit()
    await db.refresh(note)
    return note


@router.get("/absence-notes")
async def list_parent_absence_notes(
    current_user: User = Depends(require_roles(UserRole.PARENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Lists absence notes submitted by current parent."""
    stmt = (
        select(ParentAbsenceNote)
        .where(ParentAbsenceNote.parent_id == current_user.id)
        .order_by(ParentAbsenceNote.created_at.desc())
    )
    res = await db.execute(stmt)
    notes = res.scalars().all()
    return [
        {
            "id": n.id,
            "student_id": n.student_id,
            "date_from": n.date_from.isoformat(),
            "date_to": n.date_to.isoformat(),
            "reason": n.reason,
            "status": n.status,
            "created_at": n.created_at.isoformat(),
        }
        for n in notes
    ]
