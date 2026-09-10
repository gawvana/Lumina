"""Shared endpoints: i18n locales, feature flags, health check."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user
from db.models.feature_flag import FeatureFlag
from db.models.user import User
from db.session import get_db
from shared.i18n import get_locale_dict

router = APIRouter(prefix="/shared", tags=["Shared"])


@router.get("/health")
async def health_check():
    """Health check probe."""
    return {"status": "ok", "service": "Lumina School OS"}


@router.get("/locales/{lang}")
async def get_locale_strings(lang: str) -> Dict[str, Any]:
    """Returns the full translation dictionary for requested language."""
    if lang not in ["ru", "uz"]:
        lang = "ru"
    return get_locale_dict(lang)


@router.get("/feature-flags")
async def get_active_feature_flags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, bool]:
    """Returns active feature flags for the current user's school."""
    stmt = select(FeatureFlag).where(FeatureFlag.school_id == current_user.school_id)
    result = await db.execute(stmt)
    flags = result.scalars().all()
    return {f.flag_name: f.is_enabled for f in flags}
