"""Authentication service for validating Telegram WebApp initData and session tokens."""

import logging
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.schemas.auth import TokenResponse, UserProfileResponse
from api.services.invite_service import redeem_invite
from db.models.academic import Class
from db.models.feature_flag import FeatureFlag
from db.models.grading import GradingSystem
from db.models.school import School
from db.models.user import Student, User
from shared.config import settings
from shared.enums import GradingSystemType, UserRole
from shared.i18n import t
from shared.security import create_access_token, validate_telegram_init_data

logger = logging.getLogger("lumina.auth")


async def authenticate_or_register_user(
    db: AsyncSession,
    init_data_raw: str,
    invite_token: Optional[str] = None,
    bot_token: Optional[str] = None,
) -> TokenResponse:
    """
    Validates Telegram WebApp initData HMAC-SHA256 signature, resolves user,
    processes invite tokens, and issues a JWT token.
    """
    token_to_use = bot_token or settings.TELEGRAM_BOT_TOKEN
    if not token_to_use:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: TELEGRAM_BOT_TOKEN is not configured.",
        )

    validated = validate_telegram_init_data(init_data_raw, token_to_use)
    if not validated or "user" not in validated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("errors.invalid_telegram_data"),
        )

    tg_user = validated["user"]
    tg_id = int(tg_user.get("id"))
    first_name = tg_user.get("first_name", "User")
    last_name = tg_user.get("last_name")
    username = tg_user.get("username")
    lang_code = tg_user.get("language_code", "ru")
    if lang_code not in ["ru", "uz"]:
        lang_code = "ru"

    # Find user by telegram_id
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
    result = await db.execute(stmt)
    user = result.scalars().first()

    # If user doesn't exist
    if not user:
        # Check if any school exists in database. If no school exists, this is bootstrap admin!
        schools_res = await db.execute(select(School))
        first_school = schools_res.scalars().first()

        if not first_school:
            # Bootstrap initial school and default setup
            first_school = School(
                name="Lumina Demonstration School",
                code="LUMINA-01",
                settings={"country": "UZ", "timezone": settings.DEFAULT_TIMEZONE},
                is_active=True,
            )
            db.add(first_school)
            await db.flush()

            # Add default Feature Flags (all OFF)
            for flag in FeatureFlag.get_default_flags(first_school.id):
                db.add(flag)

            # Add default 5-point grading system
            gs = GradingSystem(
                school_id=first_school.id,
                name="5-балльная система",
                system_type=GradingSystemType.POINTS_5.value,
                config={"min": 1, "max": 5, "passing": 3},
                is_default=True,
            )
            db.add(gs)
            await db.flush()

            # Register first user as School Admin
            user = User(
                school_id=first_school.id,
                telegram_id=tg_id,
                role=UserRole.ADMIN.value,
                first_name=first_name,
                last_name=last_name,
                username=username,
                language_code=lang_code,
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            if invite_token:
                # Create user and redeem invite token
                user = User(
                    school_id=first_school.id,
                    telegram_id=tg_id,
                    role=UserRole.STUDENT.value,
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    language_code=lang_code,
                    is_active=True,
                )
                db.add(user)
                await db.flush()

                success, err_key = await redeem_invite(db, invite_token, user)
                if not success:
                    await db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=t(err_key or "invites.invalid", lang=lang_code),
                    )
            else:
                # No invite token provided: Check if a real Telegram Admin exists (> 10000)
                stmt_real_admin = select(User).where(
                    User.role == UserRole.ADMIN.value,
                    User.telegram_id > 10000,
                )
                existing_admin = (await db.execute(stmt_real_admin)).scalars().first()

                if not existing_admin:
                    # First real Telegram user is the Bot Creator / School Administrator!
                    user = User(
                        school_id=first_school.id,
                        telegram_id=tg_id,
                        role=UserRole.ADMIN.value,
                        first_name=first_name,
                        last_name=last_name,
                        username=username,
                        language_code=lang_code,
                        is_active=True,
                    )
                    db.add(user)
                    await db.commit()
                    await db.refresh(user)
                else:
                    # New user entering directly without invite:
                    # Enroll as Student in the school's primary class so they can immediately access the app
                    class_stmt = (
                        select(Class)
                        .where(Class.school_id == first_school.id)
                        .order_by(Class.created_at.asc())
                    )
                    default_class = (await db.execute(class_stmt)).scalars().first()

                    user = User(
                        school_id=first_school.id,
                        telegram_id=tg_id,
                        role=UserRole.STUDENT.value,
                        first_name=first_name,
                        last_name=last_name,
                        username=username,
                        language_code=lang_code,
                        is_active=True,
                    )
                    db.add(user)
                    await db.flush()

                    student_prof = Student(
                        id=user.id,
                        class_id=default_class.id if default_class else None,
                    )
                    db.add(student_prof)
                    await db.commit()
                    await db.refresh(user)
    elif invite_token:
        # Existing user redeeming a new invite token (e.g. joining class or changing role)
        success, err_key = await redeem_invite(db, invite_token, user)
        if not success:
            logger.warning("Could not redeem invite for existing user %s: %s", user.id, err_key)

    # Re-fetch user with relationships loaded
    stmt = (
        select(User)
        .where(User.id == user.id)
        .options(
            selectinload(User.school),
            selectinload(User.student_profile).selectinload(Student.student_class),
            selectinload(User.teacher_profile),
            selectinload(User.parent_profile),
        )
    )
    res = await db.execute(stmt)
    user = res.scalars().first()

    # Generate JWT
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
