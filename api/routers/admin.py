"""Admin router: school management, classes, subjects, invites, feature flags, audit."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
from db.models.user import Student, Teacher, User
from db.session import get_db
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
    stmt = select(Class).where(Class.school_id == current_user.school_id).order_by(Class.grade_level, Class.name)
    res = await db.execute(stmt)
    return res.scalars().all()


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


@router.post("/curriculum/assign")
async def assign_curriculum(
    payload: CurriculumAssignRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Assigns Teacher to teach Subject in Class."""
    link = TeacherSubjectClass(
        teacher_id=payload.teacher_id,
        subject_id=payload.subject_id,
        class_id=payload.class_id,
    )
    db.add(link)
    await db.commit()
    return {"status": "assigned"}


@router.post("/invites", response_model=InviteResponse)
async def create_invitation(
    payload: InviteCreateRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Generates an expiring invite deep-link token."""
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
    deep_link = f"https://t.me/LuminaSchoolBot?start=inv_{invite.token}"
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
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves immutable audit logs for the school."""
    stmt = (
        select(AuditLog)
        .where(AuditLog.school_id == current_user.school_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(stmt)
    return res.scalars().all()
