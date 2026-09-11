"""Teacher router: journal, grading with audit log, attendance, homework, schedule.
Enforces complete zero-trust verification on teacher assignment, classes, subjects, and students.
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.dependencies import require_roles, verify_school_isolation
from api.schemas.journal import (
    AttendanceBatchRequest,
    GradeCreateRequest,
    GradeUpdateRequest,
    HomeworkCreateRequest,
)
from api.services.audit_service import record_audit
from db.models.academic import Class, Lesson, Subject, TeacherSubjectClass
from db.models.attendance import Attendance
from db.models.grading import Grade, GradeType, GradingSystem
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


class HomeworkUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None


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
    Strictly verifies teacher is assigned to teach this class & subject.
    """
    # 1. Verify class belongs to teacher's school
    cls = await db.get(Class, class_id)
    if not cls or cls.school_id != current_user.school_id:
        raise HTTPException(status_code=404, detail=t("errors.not_found"))

    # 2. If caller is TEACHER, verify they are actively assigned to teach this class and subject
    if current_user.role == UserRole.TEACHER.value:
        tsc_stmt = select(TeacherSubjectClass).where(
            TeacherSubjectClass.teacher_id == current_user.id,
            TeacherSubjectClass.class_id == class_id,
            TeacherSubjectClass.subject_id == subject_id,
        )
        tsc_res = await db.execute(tsc_stmt)
        if not tsc_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not assigned to this class and subject",
            )

    # 3. Load students in class
    students_stmt = (
        select(Student)
        .where(Student.class_id == class_id)
        .options(selectinload(Student.user))
        .order_by(Student.student_number)
    )
    st_res = await db.execute(students_stmt)
    students = st_res.scalars().all()

    # 4. Load lessons for this class and subject
    lessons_stmt = (
        select(Lesson)
        .where(Lesson.class_id == class_id, Lesson.subject_id == subject_id)
        .order_by(Lesson.lesson_date.desc(), Lesson.period_number)
        .limit(30)
    )
    l_res = await db.execute(lessons_stmt)
    lessons = l_res.scalars().all()
    lesson_ids = [l.id for l in lessons]

    # 5. Load active grades
    grades = []
    if lesson_ids:
        grades_stmt = (
            select(Grade)
            .where(Grade.lesson_id.in_(lesson_ids), Grade.is_active == True)
            .options(selectinload(Grade.grade_type))
        )
        g_res = await db.execute(grades_stmt)
        grades = g_res.scalars().all()

    # 6. Load grade types
    gt_stmt = select(GradeType).where(GradeType.school_id == current_user.school_id)
    gt_res = await db.execute(gt_stmt)
    grade_types = gt_res.scalars().all()

    return {
        "class_id": class_id,
        "class_name": cls.name,
        "subject_id": subject_id,
        "students": [
            {
                "student_id": s.id,
                "first_name": s.user.first_name if s.user else "",
                "last_name": s.user.last_name if s.user else "",
                "number": s.student_number or "",
            }
            for s in students
            if s.user
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
    """
    Awards a grade to a student, verifying full authorization chain:
    lesson -> class -> subject -> teacher assignment -> student class enrollment -> grading scale limits.
    """
    # 1. Verify lesson exists and belongs to teacher's school
    lesson_stmt = select(Lesson).where(Lesson.id == payload.lesson_id).options(selectinload(Lesson.class_rel))
    l_res = await db.execute(lesson_stmt)
    lesson = l_res.scalars().first()
    if not lesson or not lesson.class_rel or lesson.class_rel.school_id != current_user.school_id:
        raise HTTPException(status_code=404, detail="Lesson not found or belongs to another school")

    # 2. Verify teacher assignment if caller is TEACHER
    if current_user.role == UserRole.TEACHER.value:
        tsc_stmt = select(TeacherSubjectClass).where(
            TeacherSubjectClass.teacher_id == current_user.id,
            TeacherSubjectClass.class_id == lesson.class_id,
            TeacherSubjectClass.subject_id == lesson.subject_id,
        )
        tsc_res = await db.execute(tsc_stmt)
        if not tsc_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not authorized to grade this class and subject",
            )

    # 3. Verify student exists, belongs to this school, and is enrolled in lesson's class
    student_stmt = (
        select(Student)
        .join(User, Student.id == User.id)
        .where(
            Student.id == payload.student_id,
            Student.class_id == lesson.class_id,
            User.school_id == current_user.school_id,
        )
    )
    s_res = await db.execute(student_stmt)
    student = s_res.scalars().first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is not enrolled in the lesson's class or belongs to another school",
        )

    # 4. Verify grade_type belongs to school
    grade_type = await db.get(GradeType, payload.grade_type_id)
    if not grade_type or grade_type.school_id != current_user.school_id:
        raise HTTPException(status_code=400, detail="Invalid grade type for this school")

    # 5. Validate grade value against school's GradingSystem
    gs_stmt = select(GradingSystem).where(
        GradingSystem.school_id == current_user.school_id,
        GradingSystem.is_default == True,
    )
    gs_res = await db.execute(gs_stmt)
    gs = gs_res.scalars().first()
    if gs and gs.config:
        min_val = gs.config.get("min", 1)
        max_val = gs.config.get("max", 5)
        if payload.value < min_val or payload.value > max_val:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Grade value {payload.value} is outside school grading system limits ({min_val} - {max_val})",
            )

    # 6. Create Grade
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

    # 7. Record immutable Audit Log
    await record_audit(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        entity_type=AuditEntityType.GRADE.value,
        entity_id=grade.id,
        action=AuditAction.CREATE.value,
        new_values={
            "student_id": grade.student_id,
            "lesson_id": grade.lesson_id,
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
    Verifies school isolation, teacher ownership, validates new scale value,
    and logs old & new values in AuditLog.
    """
    grade = await db.get(Grade, grade_id)
    if not grade or grade.school_id != current_user.school_id:
        raise HTTPException(status_code=404, detail="Grade not found")

    # If caller is TEACHER, verify they are the teacher who awarded the grade
    if current_user.role == UserRole.TEACHER.value and grade.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only correct grades that you personally awarded",
        )

    # Validate value limits
    gs_stmt = select(GradingSystem).where(
        GradingSystem.school_id == current_user.school_id,
        GradingSystem.is_default == True,
    )
    gs_res = await db.execute(gs_stmt)
    gs = gs_res.scalars().first()
    if gs and gs.config:
        min_val = gs.config.get("min", 1)
        max_val = gs.config.get("max", 5)
        if payload.value < min_val or payload.value > max_val:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Grade value {payload.value} is outside school limits ({min_val} - {max_val})",
            )

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
        reason=payload.reason or "Grade corrected by Teacher (Second Chance)",
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
    """Batch records attendance for a lesson with ownership and class verification."""
    lesson_stmt = select(Lesson).where(Lesson.id == payload.lesson_id).options(selectinload(Lesson.class_rel))
    l_res = await db.execute(lesson_stmt)
    lesson = l_res.scalars().first()
    if not lesson or not lesson.class_rel or lesson.class_rel.school_id != current_user.school_id:
        raise HTTPException(status_code=404, detail="Lesson not found or belongs to another school")

    if current_user.role == UserRole.TEACHER.value:
        tsc_stmt = select(TeacherSubjectClass).where(
            TeacherSubjectClass.teacher_id == current_user.id,
            TeacherSubjectClass.class_id == lesson.class_id,
            TeacherSubjectClass.subject_id == lesson.subject_id,
        )
        tsc_res = await db.execute(tsc_stmt)
        if not tsc_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not authorized for this lesson",
            )

    recorded_count = 0
    now_utc = datetime.now(timezone.utc)

    for item in payload.records:
        # Verify student is in this lesson's class
        st_stmt = select(Student).where(
            Student.id == item.student_id,
            Student.class_id == lesson.class_id,
        )
        st_res = await db.execute(st_stmt)
        if not st_res.scalars().first():
            continue

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
            record.recorded_at = now_utc
        else:
            record = Attendance(
                student_id=item.student_id,
                lesson_id=payload.lesson_id,
                status=item.status,
                note=item.note,
                recorded_by_id=current_user.id,
                recorded_at=now_utc,
            )
            db.add(record)
        recorded_count += 1

    # Record Audit Log for attendance batch
    await record_audit(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        entity_type=AuditEntityType.ATTENDANCE.value,
        entity_id=payload.lesson_id,
        action=AuditAction.CREATE.value,
        new_values={"lesson_id": payload.lesson_id, "count": recorded_count},
        reason="Batch attendance recorded by Teacher",
    )

    await db.commit()
    return {"status": "saved", "count": recorded_count}


@router.post("/homework")
async def create_homework(
    payload: HomeworkCreateRequest,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Creates homework assignment for a class with teacher curriculum verification."""
    cls = await db.get(Class, payload.class_id)
    sub = await db.get(Subject, payload.subject_id)
    if not cls or cls.school_id != current_user.school_id:
        raise HTTPException(status_code=404, detail="Class not found or belongs to another school")
    if not sub or sub.school_id != current_user.school_id:
        raise HTTPException(status_code=404, detail="Subject not found or belongs to another school")

    if current_user.role == UserRole.TEACHER.value:
        tsc_stmt = select(TeacherSubjectClass).where(
            TeacherSubjectClass.teacher_id == current_user.id,
            TeacherSubjectClass.class_id == payload.class_id,
            TeacherSubjectClass.subject_id == payload.subject_id,
        )
        tsc_res = await db.execute(tsc_stmt)
        if not tsc_res.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not authorized to assign homework for this class and subject",
            )

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
    await db.flush()

    await record_audit(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        entity_type=AuditEntityType.HOMEWORK.value,
        entity_id=hw.id,
        action=AuditAction.CREATE.value,
        new_values={
            "class_id": hw.class_id,
            "subject_id": hw.subject_id,
            "title": hw.title,
            "due_date": hw.due_date.isoformat(),
        },
        reason="Homework created by Teacher",
    )

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
        .options(
            selectinload(Homework.class_rel),
            selectinload(Homework.subject),
            selectinload(Homework.submissions),
        )
        .order_by(Homework.due_date.desc())
    )
    res = await db.execute(stmt)
    homework_list = res.scalars().all()
    return [
        {
            "id": h.id,
            "class_id": h.class_id,
            "class_name": h.class_rel.name if h.class_rel else "",
            "subject_id": h.subject_id,
            "subject_name": h.subject.name if h.subject else "",
            "title": h.title,
            "description": h.description,
            "due_date": h.due_date.isoformat(),
            "submissions_count": len(h.submissions) if h.submissions else 0,
        }
        for h in homework_list
    ]


@router.patch("/homework/{homework_id}")
async def update_teacher_homework(
    homework_id: str,
    payload: HomeworkUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Updates homework assignment."""
    hw = await db.get(Homework, homework_id)
    if not hw:
        raise HTTPException(status_code=404, detail="Homework not found")

    if current_user.role == UserRole.TEACHER.value and hw.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own homework assignments")

    if payload.title is not None:
        hw.title = payload.title
    if payload.description is not None:
        hw.description = payload.description
    if payload.due_date is not None:
        hw.due_date = payload.due_date

    await db.commit()
    await db.refresh(hw)
    return hw


@router.delete("/homework/{homework_id}")
async def delete_teacher_homework(
    homework_id: str,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Deletes homework assignment."""
    hw = await db.get(Homework, homework_id)
    if not hw:
        raise HTTPException(status_code=404, detail="Homework not found")

    if current_user.role == UserRole.TEACHER.value and hw.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own homework assignments")

    await db.delete(hw)
    await db.commit()
    return {"status": "deleted"}


class QuickGradeRequest(BaseModel):
    student_id: str
    lesson_id: str
    value: float
    grade_type: str = "classwork"
    comment: Optional[str] = None
    tag: Optional[str] = None


@router.post("/quick-grade")
async def quick_grade_student(
    payload: QuickGradeRequest,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Allows single-tap quick grading with 5-minute undo window."""
    from api.services.grade_service import award_single_grade
    return await award_single_grade(
        db=db,
        school_id=current_user.school_id,
        teacher_id=current_user.id,
        student_id=payload.student_id,
        lesson_id=payload.lesson_id,
        grade_value=payload.value,
        grade_type_code=payload.grade_type,
        comment=payload.comment,
        tag=payload.tag,
    )


@router.post("/undo-grade/{grade_id}")
async def undo_grade(
    grade_id: str,
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Allows undoing a recently awarded grade within 5 minutes."""
    from api.services.grade_service import undo_grade_submission
    return await undo_grade_submission(
        db=db,
        school_id=current_user.school_id,
        teacher_id=current_user.id,
        grade_id=grade_id,
    )
