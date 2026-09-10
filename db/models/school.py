"""School entity model."""

from typing import Any, Dict
from sqlalchemy import Boolean, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin


class School(Base, TimestampMixin):
    __tablename__ = "schools"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    settings: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    users = relationship("User", back_populates="school", cascade="all, delete-orphan")
    classes = relationship("Class", back_populates="school", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="school", cascade="all, delete-orphan")
    feature_flags = relationship("FeatureFlag", back_populates="school", cascade="all, delete-orphan")
    invites = relationship("Invite", back_populates="school", cascade="all, delete-orphan")
    grading_systems = relationship("GradingSystem", back_populates="school", cascade="all, delete-orphan")
