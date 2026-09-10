"""Student router: personal dashboard, grades, homework, schedule, analytics.
Enforces strict zero-leakage RBAC: a student can only ever receive their own data.
"""

from datetime import date
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.dependencies import require_roles
from db.models.academic import Class, Lesson, Subject
from db.models.grading import Grade, GradeType
from db.models.homework import Homework, HomeworkSubmission
from db.models.user import Student, User
from db.session import get_db
from shared.enums import HomeworkStatus, UserRole
from shared.i18n import t

router = APIRouter(
    prefix="/student",
    tags=["Student"],
    dependencies=[Depends(require_roles(UserRole.STUDENT, UserRole.ADMIN))],
)


@router.get("/dashboard")
async def get_student_dashboard(
    current_user: User = Depends(require_roles(UserRole.STUDENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns student dashboard summary: today's lessons, urgent homework, latest grade.
    Strictly isolated to current_user.
    """
    student = await db.get(Student, current_user.id)
    class_id = student.class_id if student else None

    # Today's lessons
    today = date.today()
    lessons = []
    if class_id:
        l_stmt = (
            select(Lesson)
            .where(Lesson.class_id == class_id, Lesson.lesson_date == today)
            .options(selectinload(Lesson.subject), selectinload(Lesson.teacher).selectinload(User.teacher_profile))
            .order_by(Lesson.period_number)
        )
        l_res = await db.execute(l_stmt)
        lessons = l_res.scalars().all()

    # Latest grade for this student only
    g_stmt = (
        select(Grade)
        .where(Grade.student_id == current_user.id, Grade.is_active == True)
        .options(selectinload(Grade.grade_type))
        .order_by(Grade.created_at.desc())
        .limit(1)
    )
    g_res = await db.execute(g_stmt)
    latest_grade = g_res.scalars().first()

    # Homework due soon
    homework = []
    if class_id:
        hw_stmt = (
            select(Homework)
            .where(Homework.class_id == class_id, Homework.due_date >= today)
            .options(selectinload(Homework.subject))
            .order_by(Homework.due_date)
            .limit(5)
        )
        hw_res = await db.execute(hw_stmt)
        homework = hw_res.scalars().all()

    return {
        "student": {
            "id": current_user.id,
            "name": f"{current_user.first_name} {current_user.last_name or ''}".strip(),
            "class_name": student.student_class.name if (student and student.student_class) else "",
            "xp": student.xp if student else 0,
            "level": student.level if student else 1,
        },
        "today_lessons": [
            {
                "id": l.id,
                "period": l.period_number,
                "subject": l.subject.name if l.subject else "",
                "room": l.room or "",
                "status": l.status,
            }
            for l in lessons
        ],
        "latest_grade": {
            "value": latest_grade.value,
            "raw_display": latest_grade.raw_display,
            "type": latest_grade.grade_type.name if (latest_grade and latest_grade.grade_type) else "",
            "comment": latest_grade.comment if latest_grade else None,
        } if latest_grade else None,
        "urgent_homework_count": len(homework),
    }


@router.get("/grades")
async def get_student_grades(
    student_id: Optional[str] = Query(None, description="Untrusted query param, strictly sanitized"),
    current_user: User = Depends(require_roles(UserRole.STUDENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves grades grouped by subject.
    CRITICAL SECURITY CHECK:
    If caller is STUDENT, force query to current_user.id regardless of any student_id parameter passed.
    """
    target_student_id = current_user.id
    if current_user.role == UserRole.ADMIN.value and student_id:
        target_student_id = student_id
    elif student_id and student_id != current_user.id:
        # Student explicitly tried to tamper student_id -> forbidden!
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=t("errors.access_denied", lang=current_user.language_code),
        )

    stmt = (
        select(Grade)
        .where(Grade.student_id == target_student_id, Grade.is_active == True)
        .options(selectinload(Grade.grade_type), selectinload(Grade.lesson).selectinload(Lesson.subject))
        .order_by(Grade.created_at.desc())
    )
    res = await db.execute(stmt)
    grades = res.scalars().all()

    # Group by subject
    by_subject: Dict[str, List[Any]] = {}
    for g in grades:
        sub_name = g.lesson.subject.name if (g.lesson and g.lesson.subject) else "General"
        if sub_name not in by_subject:
            by_subject[sub_name] = []
        by_subject[sub_name].append({
            "id": g.id,
            "value": g.value,
            "raw_display": g.raw_display,
            "weight": g.weight,
            "comment": g.comment,
            "is_retake": g.is_retake,
            "type_name": g.grade_type.name if g.grade_type else "",
            "date": g.created_at.date().isoformat(),
        })

    subject_summaries = []
    all_values = []
    for sub, g_list in by_subject.items():
        vals = [item["value"] for item in g_list]
        all_values.extend(vals)
        avg = round(sum(vals) / len(vals), 2) if vals else 0.0
        subject_summaries.append({
            "subject": sub,
            "average": avg,
            "grades": g_list,
        })

    overall_gpa = round(sum(all_values) / len(all_values), 2) if all_values else 0.0

    return {
        "student_id": target_student_id,
        "overall_gpa": overall_gpa,
        "subjects": subject_summaries,
    }


@router.get("/homework")
async def get_student_homework(
    current_user: User = Depends(require_roles(UserRole.STUDENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Returns homework for student's enrolled class, with personal submission statuses."""
    student = await db.get(Student, current_user.id)
    if not student or not student.class_id:
        return []

    stmt = (
        select(Homework)
        .where(Homework.class_id == student.class_id)
        .options(selectinload(Homework.subject))
        .order_by(Homework.due_date.desc())
    )
    res = await db.execute(stmt)
    homework_list = res.scalars().all()

    # Get student's submissions
    sub_stmt = select(HomeworkSubmission).where(HomeworkSubmission.student_id == current_user.id)
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


@router.patch("/homework/{homework_id}/status")
async def toggle_homework_status(
    homework_id: str,
    status_val: str = Query(..., pattern="^(TODO|DONE)$"),
    current_user: User = Depends(require_roles(UserRole.STUDENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Marks homework completed or pending for current student."""
    stmt = select(HomeworkSubmission).where(
        HomeworkSubmission.homework_id == homework_id,
        HomeworkSubmission.student_id == current_user.id,
    )
    res = await db.execute(stmt)
    submission = res.scalars().first()

    if not submission:
        submission = HomeworkSubmission(
            homework_id=homework_id,
            student_id=current_user.id,
            status=status_val,
            submitted_at=datetime.now(timezone.utc) if status_val == "DONE" else None,
        )
        db.add(submission)
    else:
        submission.status = status_val
        submission.submitted_at = datetime.now(timezone.utc) if status_val == "DONE" else None

    await db.commit()
    return {"status": submission.status}


@router.get("/schedule")
async def get_student_schedule(
    current_user: User = Depends(require_roles(UserRole.STUDENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Returns weekly timetable for student's class."""
    student = await db.get(Student, current_user.id)
    if not student or not student.class_id:
        return []

    stmt = (
        select(Lesson)
        .where(Lesson.class_id == student.class_id)
        .options(selectinload(Lesson.subject), selectinload(Lesson.teacher).selectinload(User.teacher_profile))
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


@router.get("/analytics")
async def get_student_analytics(
    current_user: User = Depends(require_roles(UserRole.STUDENT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Returns analytics: average GPA, strongest and struggling subjects."""
    stmt = (
        select(Grade)
        .where(Grade.student_id == current_user.id, Grade.is_active == True)
        .options(selectinload(Grade.lesson).selectinload(Lesson.subject))
    )
    res = await db.execute(stmt)
    grades = res.scalars().all()

    if not grades:
        return {
            "gpa": 0.0,
            "best_subject": None,
            "struggling_subject": None,
            "trend": "neutral",
            "total_grades": 0,
        }

    sub_grades: Dict[str, List[float]] = {}
    for g in grades:
        sub = g.lesson.subject.name if (g.lesson and g.lesson.subject) else "General"
        sub_grades.setdefault(sub, []).append(g.value)

    sub_avgs = {sub: sum(vals)/len(vals) for sub, vals in sub_grades.items()}
    best_sub = max(sub_avgs, key=sub_avgs.get)
    worst_sub = min(sub_avgs, key=sub_avgs.get)
    all_vals = [g.value for g in grades]
    overall_gpa = round(sum(all_vals) / len(all_vals), 2)

    return {
        "gpa": overall_gpa,
        "best_subject": {"subject": best_sub, "average": round(sub_avgs[best_sub], 2)},
        "struggling_subject": {"subject": worst_sub, "average": round(sub_avgs[worst_sub], 2)},
        "trend": "improving" if overall_gpa >= 4.0 else "steady",
        "total_grades": len(grades),
    }
