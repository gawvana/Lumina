"""Digital Backpack File Management Service."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.file import DigitalBackpackFile


async def register_file(
    db: AsyncSession,
    school_id: str,
    uploader_id: str,
    filename: str,
    file_url: str,
    mime_type: str,
    file_size_bytes: int,
    target_role: str = "STUDENT",
    subject_id: Optional[str] = None,
) -> DigitalBackpackFile:
    """Registers a file metadata record with tenant isolation."""
    file_rec = DigitalBackpackFile(
        school_id=school_id,
        uploader_id=uploader_id,
        filename=filename,
        file_url=file_url,
        mime_type=mime_type,
        file_size_bytes=file_size_bytes,
        target_role=target_role,
        subject_id=subject_id,
    )
    db.add(file_rec)
    await db.commit()
    await db.refresh(file_rec)
    return file_rec


async def list_files_for_user(
    db: AsyncSession,
    school_id: str,
    user_role: str,
    subject_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Returns accessible backpack files for the school and user role."""
    stmt = select(DigitalBackpackFile).where(
        DigitalBackpackFile.school_id == school_id,
        or_(DigitalBackpackFile.target_role == "ALL", DigitalBackpackFile.target_role == user_role),
    )
    if subject_id:
        stmt = stmt.where(DigitalBackpackFile.subject_id == subject_id)

    stmt = stmt.order_by(DigitalBackpackFile.created_at.desc())
    files = (await db.execute(stmt)).scalars().all()

    return [
        {
            "id": f.id,
            "filename": f.filename,
            "file_url": f.file_url,
            "mime_type": f.mime_type,
            "size_kb": round(f.file_size_bytes / 1024, 1),
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in files
    ]
