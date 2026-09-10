"""FastAPI dependency injection for authentication, RBAC, and school isolation."""

from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models.user import User
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
