"""Authentication router for Telegram WebApp login and user profile."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.dependencies import get_current_user
from api.schemas.auth import TelegramAuthRequest, TokenResponse, UserProfileResponse
from api.services.auth_service import authenticate_or_register_user
from db.models.user import Student, User
from db.session import get_db
from shared.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/telegram-webapp", response_model=TokenResponse)
async def login_telegram_webapp(
    payload: TelegramAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Validates Telegram WebApp initData HMAC-SHA256 signature and returns JWT access token.
    If new user with valid invite_token, binds user to school and role.
    """
    return await authenticate_or_register_user(
        db=db,
        init_data_raw=payload.init_data,
        invite_token=payload.invite_token,
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Returns the profile and active role of the currently authenticated user."""
    class_name = None
    if current_user.student_profile and current_user.student_profile.student_class:
        class_name = current_user.student_profile.student_class.name

    return UserProfileResponse(
        id=current_user.id,
        school_id=current_user.school_id,
        school_name=current_user.school.name if current_user.school else "Lumina",
        telegram_id=current_user.telegram_id,
        role=current_user.role,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        username=current_user.username,
        language_code=current_user.language_code,
        student_id=current_user.id if current_user.student_profile else None,
        teacher_id=current_user.id if current_user.teacher_profile else None,
        parent_id=current_user.id if current_user.parent_profile else None,
        class_name=class_name,
    )


from typing import Dict
from fastapi import HTTPException
from api.services.invite_service import redeem_invite
from shared.security import create_access_token
from shared.enums import UserRole
from shared.i18n import t


@router.post("/redeem-invite")
async def redeem_user_invite(
    payload: Dict[str, str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Allows an already logged-in user to redeem an invite token from the UI."""
    token = payload.get("invite_token", "").strip()
    if token.startswith("inv_"):
        token = token.replace("inv_", "", 1)
    if not token:
        raise HTTPException(status_code=400, detail="Invite token is required")

    success, err_key = await redeem_invite(db, token, current_user)
    if not success:
        raise HTTPException(status_code=400, detail=t(err_key or "invites.invalid", lang=current_user.language_code))

    return {"status": "ok", "message": "Приглашение успешно активировано"}


@router.post("/dev-token", response_model=TokenResponse)
async def get_dev_token(role: str = "STUDENT", db: AsyncSession = Depends(get_db)):
    """Allows instant role switching and preview for demonstration across roles."""
    role_tg_map = {
        UserRole.ADMIN.value: 1001,
        UserRole.TEACHER.value: 1002,
        UserRole.STUDENT.value: 2001,
        UserRole.PARENT.value: 3001,
    }
    tg_id = role_tg_map.get(role.upper(), 2001)
    stmt = (
        select(User)
        .where(User.telegram_id == tg_id)
        .options(
            selectinload(User.school),
            selectinload(User.student_profile).selectinload(Student.student_class),
            selectinload(User.teacher_profile),
            selectinload(User.parent_profile),
        )
    )
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        stmt_role = (
            select(User)
            .where(User.role == role.upper())
            .options(
                selectinload(User.school),
                selectinload(User.student_profile).selectinload(Student.student_class),
                selectinload(User.teacher_profile),
                selectinload(User.parent_profile),
            )
        )
        res_role = await db.execute(stmt_role)
        user = res_role.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail=f"No user found for role {role}")

    access_token = create_access_token(
        data={"sub": user.id, "role": user.role, "school_id": user.school_id}
    )

    class_name = None
    if user.student_profile and user.student_profile.student_class:
        class_name = user.student_profile.student_class.name

    profile = UserProfileResponse(
        id=user.id,
        school_id=user.school_id,
        school_name=user.school.name if user.school else "Lumina",
        telegram_id=user.telegram_id,
        role=user.role,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        language_code=user.language_code,
        student_id=user.id if user.student_profile else None,
        teacher_id=user.id if user.teacher_profile else None,
        parent_id=user.id if user.parent_profile else None,
        class_name=class_name,
    )
    return TokenResponse(access_token=access_token, user=profile)
