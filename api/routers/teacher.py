"""Teacher router: journal, grading with audit log, attendance, homework, schedule."""

from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.dependencies import require_roles
from api.schemas.journal import (
    AttendanceBatchRequest,
    GradeCreateRequest,
    GradeUpdateRequest,
    HomeworkCreateRequest,
)
from api.services.audit_service import record_audit
from db.models.academic import Class, Lesson, Subject, TeacherSubjectClass
from db.models.attendance import Attendance
from db.models.grading import Grade, GradeType
from db.models.homework import Homework
from db.models.user import Student, User
from db.session import get_db
from shared.enums import AttendanceStatus, AuditAction, AuditEntityType, UserRole
from shared.i18n import t

router = APIRouter(
    prefix="/teacher",
    tags=["Teacher"],
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))],
)


@router.get("/classes")
async def list_teacher_classes(
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Returns assigned classes and subjects for the teacher."""
    stmt = (
        select(TeacherSubjectClass)
        .where(TeacherSubjectClass.teacher_id == current_user.id)
        .options(
            selectinload(TeacherSubjectClass.class_rel),
            selectinload(TeacherSubjectClass.subject),
        )
    )
    res = await db.execute(stmt)
    links = res.scalars().all()
    return [
        {
            "class_id": link.class_id,
            "class_name": link.class_rel.name if link.class_rel else "",
            "subject_id": link.subject_id,
            "subject_name": link.subject.name if link.subject else "",
            "subject_code": link.subject.code if link.subject else "",
        }
        for link in links
    ]


@router.get("/journal/{class_id}/{subject_id}")
async def get_journal_data(
    class_id: str,
    subject_id: str,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns student roster, lessons, and existing grades matrix for a class/subject.
    """
    # Verify class belongs to teacher's school
    cls = await db.get(Class, class_id)
    if not cls or cls.school_id != current_user.school_id:
        raise HTTPException(status_code=404, detail=t("errors.not_found"))

    # Load students in class
    students_stmt = (
        select(Student)
        .where(Student.class_id == class_id)
        .options(selectinload(Student.user))
        .order_by(Student.student_number)
    )
    st_res = await db.execute(students_stmt)
    students = st_res.scalars().all()

    # Load lessons for this class and subject
    lessons_stmt = (
        select(Lesson)
        .where(Lesson.class_id == class_id, Lesson.subject_id == subject_id)
        .order_by(Lesson.lesson_date.desc(), Lesson.period_number)
        .limit(30)
    )
    l_res = await db.execute(lessons_stmt)
    lessons = l_res.scalars().all()
    lesson_ids = [l.id for l in lessons]

    # Load active grades
    grades = []
    if lesson_ids:
        grades_stmt = (
            select(Grade)
            .where(Grade.lesson_id.in_(lesson_ids), Grade.is_active == True)
            .options(selectinload(Grade.grade_type))
        )
        g_res = await db.execute(grades_stmt)
        grades = g_res.scalars().all()

    # Load grade types
    gt_stmt = select(GradeType).where(GradeType.school_id == current_user.school_id)
    gt_res = await db.execute(gt_stmt)
    grade_types = gt_res.scalars().all()

    return {
        "students": [
            {
                "student_id": s.id,
                "first_name": s.user.first_name if s.user else "",
                "last_name": s.user.last_name if s.user else "",
                "student_number": s.student_number or "",
            }
            for s in students
        ],
        "lessons": [
            {
                "id": l.id,
                "date": l.lesson_date.isoformat(),
                "period": l.period_number,
                "topic": l.topic or "",
            }
            for l in lessons
        ],
        "grades": [
            {
                "id": g.id,
                "student_id": g.student_id,
                "lesson_id": g.lesson_id,
                "value": g.value,
                "raw_display": g.raw_display,
                "comment": g.comment,
                "is_retake": g.is_retake,
                "type_name": g.grade_type.name if g.grade_type else "",
            }
            for g in grades
        ],
        "grade_types": [
            {"id": gt.id, "name": gt.name, "code": gt.code, "weight": gt.weight}
            for gt in grade_types
        ],
    }


@router.post("/grades")
async def award_grade(
    payload: GradeCreateRequest,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Awards a grade to a student, recording an audit log entry."""
    lesson = await db.get(Lesson, payload.lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    grade = Grade(
        school_id=current_user.school_id,
        student_id=payload.student_id,
        teacher_id=current_user.id,
        lesson_id=payload.lesson_id,
        subject_id=lesson.subject_id,
        grade_type_id=payload.grade_type_id,
        value=payload.value,
        raw_display=payload.raw_display,
        weight=payload.weight,
        comment=payload.comment,
        is_active=True,
        is_retake=False,
    )
    db.add(grade)
    await db.flush()

    await record_audit(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        entity_type=AuditEntityType.GRADE.value,
        entity_id=grade.id,
        action=AuditAction.CREATE.value,
        new_values={
            "student_id": grade.student_id,
            "value": grade.value,
            "raw_display": grade.raw_display,
            "comment": grade.comment,
        },
        reason="Grade awarded by Teacher",
    )
    await db.commit()
    await db.refresh(grade)
    return grade


@router.patch("/grades/{grade_id}")
async def update_grade(
    grade_id: str,
    payload: GradeUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    Updates or corrects a grade (Second Chance).
    Never physically deletes original; updates active record and logs old & new values in AuditLog.
    """
    grade = await db.get(Grade, grade_id)
    if not grade or grade.school_id != current_user.school_id:
        raise HTTPException(status_code=404, detail="Grade not found")

    old_values = {
        "value": grade.value,
        "raw_display": grade.raw_display,
        "comment": grade.comment,
        "is_retake": grade.is_retake,
    }

    grade.value = payload.value
    grade.raw_display = payload.raw_display
    if payload.comment is not None:
        grade.comment = payload.comment
    if payload.is_retake:
        grade.is_retake = True
    grade.updated_at = datetime.now(timezone.utc)

    await record_audit(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        entity_type=AuditEntityType.GRADE.value,
        entity_id=grade.id,
        action=AuditAction.UPDATE.value,
        old_values=old_values,
        new_values={
            "value": grade.value,
            "raw_display": grade.raw_display,
            "comment": grade.comment,
            "is_retake": grade.is_retake,
        },
        reason=payload.reason or "Grade corrected by Teacher",
    )
    await db.commit()
    await db.refresh(grade)
    return grade


@router.post("/attendance")
async def record_attendance_batch(
    payload: AttendanceBatchRequest,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Batch records attendance for a lesson."""
    lesson = await db.get(Lesson, payload.lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    for item in payload.records:
        stmt = select(Attendance).where(
            Attendance.student_id == item.student_id,
            Attendance.lesson_id == payload.lesson_id,
        )
        res = await db.execute(stmt)
        record = res.scalars().first()

        if record:
            record.status = item.status
            record.note = item.note
            record.recorded_by_id = current_user.id
            record.recorded_at = datetime.now(timezone.utc)
        else:
            record = Attendance(
                student_id=item.student_id,
                lesson_id=payload.lesson_id,
                status=item.status,
                note=item.note,
                recorded_by_id=current_user.id,
            )
            db.add(record)

    await db.commit()
    return {"status": "saved", "count": len(payload.records)}


@router.post("/homework")
async def create_homework(
    payload: HomeworkCreateRequest,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Creates homework assignment for a class."""
    hw = Homework(
        class_id=payload.class_id,
        subject_id=payload.subject_id,
        teacher_id=current_user.id,
        lesson_id=payload.lesson_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
    )
    db.add(hw)
    await db.commit()
    await db.refresh(hw)
    return hw


@router.get("/homework")
async def list_teacher_homework(
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Lists homework created by the teacher."""
    stmt = (
        select(Homework)
        .where(Homework.teacher_id == current_user.id)
        .options(selectinload(Homework.class_rel), selectinload(Homework.subject))
        .order_by(Homework.due_date.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()
