"""Invite token model for single-use expiring invitation links."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin
from shared.enums import UserRole


class Invite(Base, TimestampMixin):
    __tablename__ = "invites"

    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.STUDENT.value)
    target_class_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("classes.id", ondelete="SET NULL"), nullable=True)
    target_student_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("students.id", ondelete="SET NULL"), nullable=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    current_uses: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Relationships
    school = relationship("School", back_populates="invites")

    def is_valid(self) -> bool:
        """Returns True if the invite is active, unexpired, and has remaining uses."""
        if not self.is_active:
            return False
        if self.current_uses >= self.max_uses:
            return False
        now = datetime.now(timezone.utc)
        # Handle naive or aware datetimes
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now < exp
