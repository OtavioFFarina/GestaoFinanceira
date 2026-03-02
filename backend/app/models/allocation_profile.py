"""
AllocationProfile model — stores personalized budget allocation rules (e.g. 50/30/20).
Rules stored as JSONB for flexibility without schema migrations.
"""
from typing import TYPE_CHECKING, Any, Dict

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.user import User


class AllocationProfile(Base, TimestampMixin):
    __tablename__ = "allocation_profiles"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # JSON structure example:
    # {"fixed_expenses": 50, "investments": 20, "education": 10, "leisure": 15, "savings": 5}
    # Values must sum to 100 (enforced at service/application layer)
    rules: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="allocation_profiles")

    def __repr__(self) -> str:
        return f"<AllocationProfile id={self.id} name={self.name} active={self.is_active}>"
