"""
MonthlyRecord model — one row per user per month for financial tracking.
Enforces unique constraint (user_id, reference_month) at DB level.
"""
from typing import TYPE_CHECKING, List

from sqlalchemy import Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.record_category import RecordCategory


class MonthlyRecord(Base, TimestampMixin):
    __tablename__ = "monthly_records"
    __table_args__ = (
        UniqueConstraint("user_id", "reference_month", name="uq_user_month"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # First day of the reference month — stored as DATE (e.g., 2024-03-01)
    reference_month: Mapped[Date] = mapped_column(Date, nullable=False)
    # Total income for the month
    total_received: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, default=0.00
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="monthly_records")
    categories: Mapped[List["RecordCategory"]] = relationship(
        "RecordCategory", back_populates="record", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MonthlyRecord id={self.id} month={self.reference_month}>"
