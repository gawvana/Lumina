"""Grade Management Service: Quick Grading, Batch Grading, 5-minute Undo, and Second Chance."""

from datetime import datetime, timezone, timedelta
import logging
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.services.audit_service import record_audit
from api.services.xp_service import award_xp
from db.models.academic import Lesson, Subject, TeacherSubjectClass
from db.models.grading import Grade, GradeType
from db.models.user import Student, User

logger = logging.getLogger("lumina.grading")


async def award_single_grade(
    db: AsyncSession,
    school_id: str,
    teacher_id: str,
    student_id: str,
    lesson_id: str,
    grade_value: float,
    grade_type_code: str = "classwork",
    comment: Optional[str] = None,
    tag: Optional[str] = None,
) -> Dict[str, Any]:
    """Awards a grade with audit trail and XP reward for the student."""
    # Verify student exists in same school
    st_stmt = (
        select(Student)
        .join(User, User.id == Student.id)
        .where(Student.id == student_id, User.school_id == school_id)
        .options(selectinload(Student.user))
    )
    student = (await db.execute(st_stmt)).scalars().first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found in school")

    # Verify lesson belongs to school
    lesson_stmt = (
        select(Lesson)
        .join(Subject, Subject.id == Lesson.subject_id)
        .where(Lesson.id == lesson_id, Subject.school_id == school_id)
    )
    lesson = (await db.execute(lesson_stmt)).scalars().first()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found in school")

    # Find matching GradeType or fallback
    gt_stmt = select(GradeType).where(GradeType.school_id == school_id)
    grade_types = (await db.execute(gt_stmt)).scalars().all()
    target_gt = next((gt for gt in grade_types if gt.code.lower() == grade_type_code.lower()), None)
    if not target_gt:
        target_gt = grade_types[0] if grade_types else None
    
    if not target_gt:
        target_gt = GradeType(
            school_id=school_id,
            name="Классная работа",
            code="classwork",
            weight=1.0,
        )
        db.add(target_gt)
        await db.flush()

    raw_display = str(int(grade_value)) if grade_value.is_integer() else str(grade_value)

    grade = Grade(
        school_id=school_id,
        student_id=student_id,
        lesson_id=lesson_id,
        subject_id=lesson.subject_id,
        grade_type_id=target_gt.id,
        teacher_id=teacher_id,
        value=grade_value,
        raw_display=raw_display,
        weight=target_gt.weight,
        comment=comment,
        is_active=True,
        is_retake=False,
    )
    db.add(grade)
    await db.flush()

    # Log audit event
    await record_audit(
        db=db,
        school_id=school_id,
        user_id=teacher_id,
        action="CREATE",
        entity_type="grade",
        entity_id=grade.id,
        new_values={"value": grade_value, "student_id": student_id, "type": target_gt.code, "comment": comment},
        reason="Teacher quick grade",
    )

    # Award XP to student for good performance
    xp_amount = 20 if grade_value >= 4.0 else 10
    await award_xp(db, school_id, student_id, xp_amount, f"Оценка {raw_display} за урок", source="grade")

    await db.commit()
    await db.refresh(grade)

    return {
        "id": grade.id,
        "value": grade.value,
        "student_id": grade.student_id,
        "lesson_id": grade.lesson_id,
        "comment": grade.comment,
        "created_at": grade.created_at.isoformat() if grade.created_at else None,
        "undo_available": True,
        "xp_awarded": xp_amount,
    }


async def undo_grade_submission(
    db: AsyncSession,
    school_id: str,
    teacher_id: str,
    grade_id: str,
) -> Dict[str, Any]:
    """Allows a teacher to undo a grade within a 5-minute safety window."""
    stmt = select(Grade).where(
        Grade.id == grade_id,
        Grade.school_id == school_id,
        Grade.teacher_id == teacher_id,
    )
    grade = (await db.execute(stmt)).scalars().first()
    if not grade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grade not found or unauthorized")

    # Check 5-minute window
    now = datetime.now(timezone.utc)
    grade_created = grade.created_at.replace(tzinfo=timezone.utc) if grade.created_at.tzinfo is None else grade.created_at
    if now - grade_created > timedelta(minutes=5):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Период быстрой отмены (5 минут) истек")

    old_values = {"value": grade.value, "student_id": grade.student_id}
    await db.delete(grade)

    await record_audit(
        db=db,
        school_id=school_id,
        user_id=teacher_id,
        action="DELETE",
        entity_type="grade",
        entity_id=grade_id,
        old_values=old_values,
        reason="Teacher quick grade undo",
    )
    await db.commit()

    return {"status": "undone", "message": "Оценка успешно отменена", "grade_id": grade_id}
