"""Digital Backpack: Educational file storage and metadata models."""

from typing import Optional
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, TimestampMixin


class DigitalBackpackFile(Base, TimestampMixin):
    """File metadata record with tenant isolation and access control."""
    __tablename__ = "digital_backpack_files"

    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    uploader_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_role: Mapped[str] = mapped_column(String(20), default="STUDENT", nullable=False)  # ALL, STUDENT, TEACHER
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    subject_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
