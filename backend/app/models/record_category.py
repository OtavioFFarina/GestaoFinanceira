"""
RecordCategory model — stores planned vs actual spending per category per month.
Uses Python Enum for type safety at both ORM and DB level.
"""
import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_uuid

if TYPE_CHECKING:
    from app.models.monthly_record import MonthlyRecord


class CategoryEnum(str, enum.Enum):
    FIXED_EXPENSES = "fixed_expenses"
    INVESTMENTS = "investments"
    EDUCATION = "education"
    LEISURE = "leisure"
    SAVINGS = "savings"
    OTHER = "other"


class RecordCategory(Base):
    __tablename__ = "record_categories"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    record_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("monthly_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[CategoryEnum] = mapped_column(
        SAEnum(CategoryEnum, name="category_enum"), nullable=False
    )
    # Planned budget for this category
    planned_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    # Actual amount spent/invested
    actual_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    record: Mapped["MonthlyRecord"] = relationship(
        "MonthlyRecord", back_populates="categories"
    )

    def __repr__(self) -> str:
        return (
            f"<RecordCategory id={self.id} category={self.category} "
            f"planned={self.planned_amount} actual={self.actual_amount}>"
        )
