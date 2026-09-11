"""Digital Backpack File Storage Router."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user
from api.services.file_service import list_files_for_user, register_file
from db.models.user import User
from db.session import get_db

router = APIRouter(prefix="/backpack", tags=["Digital Backpack"])


class FileRegisterPayload(BaseModel):
    filename: str
    file_url: str
    mime_type: str = "application/pdf"
    file_size_bytes: int = 102400
    target_role: str = "STUDENT"
    subject_id: Optional[str] = None


@router.get("/files")
async def get_my_backpack_files(
    subject_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists files accessible to the current user with school isolation."""
    return await list_files_for_user(
        db=db,
        school_id=current_user.school_id,
        user_role=current_user.role,
        subject_id=subject_id,
    )


@router.post("/files")
async def add_file_to_backpack(
    payload: FileRegisterPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Registers a new educational document in the school's digital backpack."""
    rec = await register_file(
        db=db,
        school_id=current_user.school_id,
        uploader_id=current_user.id,
        filename=payload.filename,
        file_url=payload.file_url,
        mime_type=payload.mime_type,
        file_size_bytes=payload.file_size_bytes,
        target_role=payload.target_role,
        subject_id=payload.subject_id,
    )
    return {"status": "ok", "file_id": rec.id, "filename": rec.filename}
