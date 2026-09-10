"""Feature Flags model per-school."""

from typing import Any, Dict
from sqlalchemy import Boolean, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin
from shared.enums import FeatureFlagName


class FeatureFlag(Base, TimestampMixin):
    __tablename__ = "feature_flags"
    __table_args__ = (
        UniqueConstraint("school_id", "flag_name", name="uq_school_flag_name"),
    )

    school_id: Mapped[str] = mapped_column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    flag_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    school = relationship("School", back_populates="feature_flags")

    @classmethod
    def get_default_flags(cls, school_id: str):
        """Returns default FeatureFlag entities (all OFF by default per specification)."""
        return [
            cls(school_id=school_id, flag_name=flag.value, is_enabled=False, config={})
            for flag in FeatureFlagName
        ]
