"""Admin request and response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SchoolCreateRequest(BaseModel):
    name: str
    code: str


class ClassCreateRequest(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "7-A"})
    grade_level: int = Field(..., ge=1, le=12)
    academic_year: str = Field(..., json_schema_extra={"example": "2026-2027"})


class SubjectCreateRequest(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Алгебра"})
    code: str = Field(..., json_schema_extra={"example": "ALG"})


class CurriculumAssignRequest(BaseModel):
    teacher_id: str
    subject_id: str
    class_id: str


class InviteCreateRequest(BaseModel):
    role: str = Field(..., json_schema_extra={"example": "STUDENT"})
    target_class_id: Optional[str] = None
    target_student_id: Optional[str] = None
    duration_hours: int = Field(default=24, ge=1, le=720)
    max_uses: int = Field(default=1, ge=1)


class InviteResponse(BaseModel):
    id: str
    token: str
    deep_link: str
    role: str
    expires_at: datetime
    max_uses: int
    current_uses: int
    is_active: bool


class FeatureFlagUpdateRequest(BaseModel):
    flag_name: str
    is_enabled: bool
    config: Optional[Dict[str, Any]] = None


class SchoolOverviewResponse(BaseModel):
    total_students: int
    total_teachers: int
    total_classes: int
    daily_attendance_rate: float
