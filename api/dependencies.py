"""FastAPI dependency injection for authentication, RBAC, and school isolation."""

from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models.academic import Class, Lesson, Subject, TeacherSubjectClass
from db.models.user import Student, User
from db.session import get_db
from shared.enums import UserRole
from shared.i18n import t
from shared.security import decode_access_token

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extracts and verifies JWT Bearer token and returns authenticated User."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("errors.unauthorized"),
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("errors.unauthorized"),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.school),
            selectinload(User.student_profile),
            selectinload(User.teacher_profile),
            selectinload(User.parent_profile),
        )
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("errors.unauthorized"),
        )

    return user


def require_roles(*allowed_roles: UserRole):
    """Dependency factory restricting endpoint to specific UserRoles."""
    allowed_values = [r.value if isinstance(r, UserRole) else str(r) for r in allowed_roles]

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=t("errors.forbidden", lang=current_user.language_code),
            )
        return current_user

    return role_checker


def verify_school_isolation(current_user: User, target_school_id: str) -> None:
    """Prevents cross-school data leaks even if IDs are tampered with."""
    if current_user.school_id != target_school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=t("errors.school_mismatch", lang=current_user.language_code),
        )


async def verify_teacher_assignment(
    db: AsyncSession,
    teacher_id: str,
    class_id: str,
    subject_id: str,
) -> bool:
    """Verifies that teacher is actively assigned to teach subject in class."""
    stmt = select(TeacherSubjectClass).where(
        TeacherSubjectClass.teacher_id == teacher_id,
        TeacherSubjectClass.class_id == class_id,
        TeacherSubjectClass.subject_id == subject_id,
    )
    res = await db.execute(stmt)
    return res.scalars().first() is not None


async def verify_student_in_class(
    db: AsyncSession,
    student_id: str,
    class_id: str,
    school_id: str,
) -> Student:
    """Verifies that student belongs to the school and is enrolled in the given class."""
    stmt = (
        select(Student)
        .join(User, Student.id == User.id)
        .where(
            Student.id == student_id,
            Student.class_id == class_id,
            User.school_id == school_id,
        )
    )
    res = await db.execute(stmt)
    student = res.scalars().first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is not enrolled in this class or school mismatch",
        )
    return student
