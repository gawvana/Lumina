"""Admin router: school management, classes, subjects, curriculum, invites, feature flags, audit."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.dependencies import require_roles
from api.schemas.admin import (
    ClassCreateRequest,
    CurriculumAssignRequest,
    FeatureFlagUpdateRequest,
    InviteCreateRequest,
    InviteResponse,
    SchoolOverviewResponse,
    SubjectCreateRequest,
)
from api.services.audit_service import record_audit
from api.services.invite_service import create_invite
from db.models.academic import Class, Subject, TeacherSubjectClass
from db.models.audit import AuditLog
from db.models.feature_flag import FeatureFlag
from db.models.invite import Invite
from db.models.user import Parent, Student, StudentParent, Teacher, User
from db.session import get_db
from shared.config import settings
from shared.enums import AuditAction, AuditEntityType, UserRole
from shared.i18n import t

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_roles(UserRole.ADMIN))])


@router.get("/overview", response_model=SchoolOverviewResponse)
async def get_school_overview(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Returns high-level statistics for the school."""
    sid = current_user.school_id

    students_cnt = await db.scalar(
        select(func.count(Student.id)).join(User).where(User.school_id == sid)
    ) or 0
    teachers_cnt = await db.scalar(
        select(func.count(Teacher.id)).join(User).where(User.school_id == sid)
    ) or 0
    classes_cnt = await db.scalar(
        select(func.count(Class.id)).where(Class.school_id == sid)
    ) or 0

    return SchoolOverviewResponse(
        total_students=students_cnt,
        total_teachers=teachers_cnt,
        total_classes=classes_cnt,
        daily_attendance_rate=96.4,
    )


@router.get("/classes")
async def list_classes(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Lists all classes in the school."""
    stmt = (
        select(Class)
        .where(Class.school_id == current_user.school_id)
        .options(selectinload(Class.students))
        .order_by(Class.grade_level, Class.name)
    )
    res = await db.execute(stmt)
    classes = res.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "grade_level": c.grade_level,
            "academic_year": c.academic_year,
            "students_count": len(c.students),
        }
        for c in classes
    ]


@router.post("/classes")
async def create_class(
    payload: ClassCreateRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Creates an academic class."""
    new_class = Class(
        school_id=current_user.school_id,
        name=payload.name,
        grade_level=payload.grade_level,
        academic_year=payload.academic_year,
    )
    db.add(new_class)
    await db.flush()

    await record_audit(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        entity_type=AuditEntityType.CLASS.value,
        entity_id=new_class.id,
        action=AuditAction.CREATE.value,
        new_values={"name": payload.name, "grade_level": payload.grade_level},
        reason="Class created by Admin",
    )
    await db.commit()
    await db.refresh(new_class)
    return new_class


@router.get("/subjects")
async def list_subjects(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Lists all subjects in the school."""
    stmt = select(Subject).where(Subject.school_id == current_user.school_id).order_by(Subject.name)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/subjects")
async def create_subject(
    payload: SubjectCreateRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Creates a subject."""
    new_sub = Subject(
        school_id=current_user.school_id,
        name=payload.name,
        code=payload.code,
    )
    db.add(new_sub)
    await db.flush()

    await record_audit(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        entity_type=AuditEntityType.SUBJECT.value,
        entity_id=new_sub.id,
        action=AuditAction.CREATE.value,
        new_values={"name": payload.name, "code": payload.code},
        reason="Subject created by Admin",
    )
    await db.commit()
    await db.refresh(new_sub)
    return new_sub


@router.get("/curriculum")
async def list_curriculum_assignments(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Lists all teacher-subject-class assignments for current school."""
    stmt = (
        select(TeacherSubjectClass)
        .join(Class, TeacherSubjectClass.class_id == Class.id)
        .where(Class.school_id == current_user.school_id)
        .options(
            selectinload(TeacherSubjectClass.class_rel),
            selectinload(TeacherSubjectClass.subject),
            selectinload(TeacherSubjectClass.teacher).selectinload(Teacher.user),
        )
    )
    res = await db.execute(stmt)
    links = res.scalars().all()
    return [
        {
            "id": link.id,
            "teacher_id": link.teacher_id,
            "teacher_name": f"{link.teacher.user.first_name} {link.teacher.user.last_name or ''}".strip() if link.teacher and link.teacher.user else "",
            "class_id": link.class_id,
            "class_name": link.class_rel.name if link.class_rel else "",
            "subject_id": link.subject_id,
            "subject_name": link.subject.name if link.subject else "",
        }
        for link in links
    ]


@router.post("/curriculum/assign")
async def assign_curriculum(
    payload: CurriculumAssignRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    Assigns Teacher to teach Subject in Class.
    CRITICAL: Validates that teacher, subject, and class ALL belong to the admin's school.
    """
    t_user = await db.get(User, payload.teacher_id)
    if not t_user or t_user.school_id != current_user.school_id or t_user.role != UserRole.TEACHER.value:
        raise HTTPException(status_code=400, detail="Teacher not found in this school")

    sub = await db.get(Subject, payload.subject_id)
    if not sub or sub.school_id != current_user.school_id:
        raise HTTPException(status_code=400, detail="Subject not found in this school")

    cls = await db.get(Class, payload.class_id)
    if not cls or cls.school_id != current_user.school_id:
        raise HTTPException(status_code=400, detail="Class not found in this school")

    # Check for duplicate
    existing = await db.execute(
        select(TeacherSubjectClass).where(
            TeacherSubjectClass.teacher_id == payload.teacher_id,
            TeacherSubjectClass.subject_id == payload.subject_id,
            TeacherSubjectClass.class_id == payload.class_id,
        )
    )
    if existing.scalars().first():
        return {"status": "already_assigned"}

    link = TeacherSubjectClass(
        teacher_id=payload.teacher_id,
        subject_id=payload.subject_id,
        class_id=payload.class_id,
    )
    db.add(link)
    await db.flush()

    await record_audit(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        entity_type=AuditEntityType.CLASS.value,
        entity_id=link.id,
        action=AuditAction.CREATE.value,
        new_values={
            "teacher_id": payload.teacher_id,
            "subject_id": payload.subject_id,
            "class_id": payload.class_id,
        },
        reason="Curriculum assigned by Admin",
    )

    await db.commit()
    return {"status": "assigned"}


@router.get("/teachers")
async def list_teachers(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Lists teachers in the school with profile details."""
    stmt = (
        select(Teacher)
        .join(User, Teacher.id == User.id)
        .where(User.school_id == current_user.school_id)
        .options(selectinload(Teacher.user))
    )
    res = await db.execute(stmt)
    teachers = res.scalars().all()
    return [
        {
            "id": t.id,
            "name": f"{t.user.first_name} {t.user.last_name or ''}".strip(),
            "username": t.user.username or "",
            "title": t.title or "",
            "bio": t.bio or "",
        }
        for t in teachers
        if t.user
    ]


@router.get("/students")
async def list_students(
    class_id: Optional[str] = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Lists students in the school with class info."""
    stmt = (
        select(Student)
        .join(User, Student.id == User.id)
        .where(User.school_id == current_user.school_id)
        .options(selectinload(Student.user), selectinload(Student.student_class))
    )
    if class_id:
        stmt = stmt.where(Student.class_id == class_id)
    res = await db.execute(stmt)
    students = res.scalars().all()
    return [
        {
            "id": s.id,
            "name": f"{s.user.first_name} {s.user.last_name or ''}".strip(),
            "class_id": s.class_id or "",
            "class_name": s.student_class.name if s.student_class else "",
            "student_number": s.student_number or "",
            "xp": s.xp,
            "level": s.level,
        }
        for s in students
        if s.user
    ]


@router.get("/parents")
async def list_parents(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Lists parents in the school with linked children info."""
    stmt = (
        select(Parent)
        .join(User, Parent.id == User.id)
        .where(User.school_id == current_user.school_id)
        .options(
            selectinload(Parent.user),
            selectinload(Parent.children_links).selectinload(StudentParent.student).selectinload(Student.user),
        )
    )
    res = await db.execute(stmt)
    parents = res.scalars().all()
    return [
        {
            "id": p.id,
            "name": f"{p.user.first_name} {p.user.last_name or ''}".strip(),
            "phone_number": p.phone_number or "",
            "children": [
                {
                    "student_id": link.student_id,
                    "student_name": f"{link.student.user.first_name} {link.student.user.last_name or ''}".strip() if link.student and link.student.user else "",
                }
                for link in p.children_links
            ],
        }
        for p in parents
        if p.user
    ]


@router.get("/invites")
async def list_invites(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Lists active and expired invites for the school."""
    stmt = (
        select(Invite)
        .where(Invite.school_id == current_user.school_id)
        .order_by(Invite.created_at.desc())
        .limit(50)
    )
    res = await db.execute(stmt)
    invites = res.scalars().all()
    return [
        {
            "id": inv.id,
            "token": inv.token,
            "deep_link": f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start=inv_{inv.token}",
            "role": inv.role,
            "expires_at": inv.expires_at.isoformat(),
            "max_uses": inv.max_uses,
            "current_uses": inv.current_uses,
            "is_active": inv.is_active,
        }
        for inv in invites
    ]


@router.post("/invites", response_model=InviteResponse)
async def create_invitation(
    payload: InviteCreateRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Generates an expiring invite deep-link token with tenant entity checks."""
    invite = await create_invite(
        db=db,
        school_id=current_user.school_id,
        role=payload.role,
        created_by_id=current_user.id,
        duration_hours=payload.duration_hours,
        max_uses=payload.max_uses,
        target_class_id=payload.target_class_id,
        target_student_id=payload.target_student_id,
    )
    deep_link = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start=inv_{invite.token}"
    return InviteResponse(
        id=invite.id,
        token=invite.token,
        deep_link=deep_link,
        role=invite.role,
        expires_at=invite.expires_at,
        max_uses=invite.max_uses,
        current_uses=invite.current_uses,
        is_active=invite.is_active,
    )


@router.get("/feature-flags")
async def list_feature_flags(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Lists all feature flags for the school."""
    stmt = select(FeatureFlag).where(FeatureFlag.school_id == current_user.school_id)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.patch("/feature-flags")
async def update_feature_flag(
    payload: FeatureFlagUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Toggles a school feature flag dynamically without redeployment."""
    stmt = select(FeatureFlag).where(
        FeatureFlag.school_id == current_user.school_id,
        FeatureFlag.flag_name == payload.flag_name,
    )
    res = await db.execute(stmt)
    flag = res.scalars().first()

    if not flag:
        flag = FeatureFlag(
            school_id=current_user.school_id,
            flag_name=payload.flag_name,
            is_enabled=payload.is_enabled,
            config=payload.config or {},
        )
        db.add(flag)
    else:
        old_val = flag.is_enabled
        flag.is_enabled = payload.is_enabled
        if payload.config is not None:
            flag.config = payload.config

        await record_audit(
            db=db,
            school_id=current_user.school_id,
            user_id=current_user.id,
            entity_type=AuditEntityType.FEATURE_FLAG.value,
            entity_id=flag.id,
            action=AuditAction.UPDATE.value,
            old_values={"is_enabled": old_val},
            new_values={"is_enabled": payload.is_enabled},
            reason=f"Feature flag {payload.flag_name} updated by Admin",
        )

    await db.commit()
    await db.refresh(flag)
    return flag


@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 50,
    offset: int = 0,
    entity_type: Optional[str] = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves immutable audit logs for the school with optional entity filter."""
    stmt = (
        select(AuditLog)
        .where(AuditLog.school_id == current_user.school_id)
        .order_by(AuditLog.created_at.desc())
    )
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    stmt = stmt.limit(limit).offset(offset)
    res = await db.execute(stmt)
    logs = res.scalars().all()
    return [
        {
            "id": log.id,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "action": log.action,
            "old_values": log.old_values,
            "new_values": log.new_values,
            "reason": log.reason,
            "user_id": log.user_id,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
