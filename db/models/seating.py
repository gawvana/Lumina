"""Interactive Classroom Seating Grid models."""

from typing import Optional
from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin


class DeskSeating(Base, TimestampMixin):
    """Represents a student desk position inside a classroom layout."""
    __tablename__ = "desk_seatings"
    __table_args__ = (
        UniqueConstraint("class_id", "row_num", "col_num", name="uq_class_desk_position"),
    )

    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id: Mapped[str] = mapped_column(String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("students.id", ondelete="SET NULL"), nullable=True, index=True)
    row_num: Mapped[int] = mapped_column(Integer, nullable=False)
    col_num: Mapped[int] = mapped_column(Integer, nullable=False)
    desk_label: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_empty: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    student = relationship("Student")
