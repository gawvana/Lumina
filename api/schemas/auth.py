"""Authentication request and response schemas."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class TelegramAuthRequest(BaseModel):
    init_data: str = Field(..., description="Raw Telegram WebApp initData string")
    invite_token: Optional[str] = Field(None, description="Optional deep link invite token for new user onboarding")


class UserProfileResponse(BaseModel):
    id: str
    school_id: str
    school_name: str
    telegram_id: int
    role: str
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: str
    student_id: Optional[str] = None
    teacher_id: Optional[str] = None
    parent_id: Optional[str] = None
    class_name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse
