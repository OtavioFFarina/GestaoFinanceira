"""
Transaction model — individual financial transactions within a monthly record.
"""
import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean, Date, DateTime, Enum as SAEnum, ForeignKey,
    Numeric, String, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_uuid

if TYPE_CHECKING:
    from app.models.monthly_record import MonthlyRecord
    from app.models.category import Category
    from app.models.goal import Goal


class TransactionTypeEnum(str, enum.Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    record_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("monthly_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    goal_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("goals.id", ondelete="SET NULL"),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    type: Mapped[TransactionTypeEnum] = mapped_column(
        SAEnum(TransactionTypeEnum, name="transaction_type_enum"), nullable=False
    )
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    recurring: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    record: Mapped["MonthlyRecord"] = relationship("MonthlyRecord", backref="transactions")
    category: Mapped["Category"] = relationship("Category", lazy="joined")
    goal: Mapped[Optional["Goal"]] = relationship("Goal", backref="transactions")

    def __repr__(self) -> str:
        return f"<Transaction id={self.id} amount={self.amount} type={self.type}>"
