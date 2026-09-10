"""Teacher Journal, Grades, Attendance, and Homework schemas."""

from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


class GradeCreateRequest(BaseModel):
    student_id: str
    lesson_id: str
    grade_type_id: str
    value: float = Field(..., json_schema_extra={"example": 5.0})
    raw_display: str = Field(..., json_schema_extra={"example": "5"})
    comment: Optional[str] = None
    weight: float = 1.0


class GradeUpdateRequest(BaseModel):
    value: float
    raw_display: str
    comment: Optional[str] = None
    is_retake: bool = False
    reason: Optional[str] = "Correction"


class AttendanceRecordItem(BaseModel):
    student_id: str
    status: str = Field(..., json_schema_extra={"example": "PRESENT"})  # PRESENT, ABSENT, LATE, EXCUSED
    note: Optional[str] = None


class AttendanceBatchRequest(BaseModel):
    lesson_id: str
    records: List[AttendanceRecordItem]


class HomeworkCreateRequest(BaseModel):
    class_id: str
    subject_id: str
    lesson_id: Optional[str] = None
    title: str
    description: str
    due_date: date


class AbsenceNoteCreateRequest(BaseModel):
    student_id: str
    date_from: date
    date_to: date
    reason: str
