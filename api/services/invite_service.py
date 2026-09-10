"""Invite service for creating and redeeming single-use expiring invite tokens."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.audit import AuditLog
from db.models.invite import Invite
from db.models.user import Parent, Student, StudentParent, Teacher, User
from shared.enums import AuditAction, AuditEntityType, UserRole


async def create_invite(
    db: AsyncSession,
    school_id: str,
    role: str,
    created_by_id: Optional[str] = None,
    duration_hours: int = 24,
    max_uses: int = 1,
    target_class_id: Optional[str] = None,
    target_student_id: Optional[str] = None,
) -> Invite:
    """Generates an expiring, single-use invite token."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)

    invite = Invite(
        school_id=school_id,
        token=token,
        role=role,
        target_class_id=target_class_id,
        target_student_id=target_student_id,
        expires_at=expires_at,
        max_uses=max_uses,
        current_uses=0,
        is_active=True,
        created_by_id=created_by_id,
    )
    db.add(invite)
    await db.flush()

    # Record Audit Log
    audit = AuditLog(
        id=secrets.token_hex(18),
        school_id=school_id,
        user_id=created_by_id,
        entity_type=AuditEntityType.INVITE.value,
        entity_id=invite.id,
        action=AuditAction.CREATE.value,
        new_values={"role": role, "expires_at": expires_at.isoformat(), "max_uses": max_uses},
        reason="Invite token generated",
    )
    db.add(audit)
    await db.commit()
    await db.refresh(invite)
    return invite


async def redeem_invite(
    db: AsyncSession,
    token: str,
    user: User,
) -> Tuple[bool, Optional[str]]:
    """
    Redeems an invite token, binds the user to the school and role,
    and updates the invite usage count.
    """
    stmt = select(Invite).where(Invite.token == token)
    result = await db.execute(stmt)
    invite = result.scalars().first()

    if not invite:
        return False, "invites.invalid"

    if not invite.is_valid():
        return False, "invites.expired" if datetime.now(timezone.utc) >= invite.expires_at.replace(tzinfo=timezone.utc) else "invites.already_used"

    # Bind user to school and role
    old_school = user.school_id
    old_role = user.role

    user.school_id = invite.school_id
    user.role = invite.role

    # Create role-specific sub-profile if not exists
    if invite.role == UserRole.STUDENT.value:
        existing_student = await db.get(Student, user.id)
        if not existing_student:
            student = Student(id=user.id, class_id=invite.target_class_id)
            db.add(student)
        elif invite.target_class_id:
            existing_student.class_id = invite.target_class_id

    elif invite.role == UserRole.TEACHER.value:
        existing_teacher = await db.get(Teacher, user.id)
        if not existing_teacher:
            teacher = Teacher(id=user.id)
            db.add(teacher)

    elif invite.role == UserRole.PARENT.value:
        existing_parent = await db.get(Parent, user.id)
        if not existing_parent:
            parent = Parent(id=user.id)
            db.add(parent)
        if invite.target_student_id:
            link_stmt = select(StudentParent).where(
                StudentParent.parent_id == user.id,
                StudentParent.student_id == invite.target_student_id,
            )
            link_res = await db.execute(link_stmt)
            if not link_res.scalars().first():
                link = StudentParent(
                    student_id=invite.target_student_id,
                    parent_id=user.id,
                    relationship_type="guardian",
                    is_confirmed=True,
                )
                db.add(link)

    # Increment invite uses
    invite.current_uses += 1
    if invite.current_uses >= invite.max_uses:
        invite.is_active = False

    # Record Audit Log
    audit = AuditLog(
        id=secrets.token_hex(18),
        school_id=invite.school_id,
        user_id=user.id,
        entity_type=AuditEntityType.INVITE.value,
        entity_id=invite.id,
        action=AuditAction.UPDATE.value,
        old_values={"school_id": old_school, "role": old_role},
        new_values={"school_id": user.school_id, "role": user.role, "uses": invite.current_uses},
        reason=f"Invite token redeemed by user {user.telegram_id}",
    )
    db.add(audit)
    await db.commit()
    return True, None
