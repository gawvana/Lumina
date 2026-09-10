"""Authentication router for Telegram WebApp login and user profile."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user
from api.schemas.auth import TelegramAuthRequest, TokenResponse, UserProfileResponse
from api.services.auth_service import authenticate_or_register_user
from db.models.user import Student, User
from db.session import get_db

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
