"""
Installment model — individual payment installments within a financial contract.
"""
import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date, DateTime, Enum as SAEnum, ForeignKey, Integer,
    Numeric, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_uuid

if TYPE_CHECKING:
    from app.models.financial_contract import FinancialContract


class InstallmentStatusEnum(str, enum.Enum):
    PENDENTE = "pendente"
    PAGA = "paga"
    ATRASADA = "atrasada"


class Installment(Base):
    __tablename__ = "installments"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    contract_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("financial_contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[InstallmentStatusEnum] = mapped_column(
        SAEnum(InstallmentStatusEnum, name="installment_status_enum"),
        nullable=False,
        default=InstallmentStatusEnum.PENDENTE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    contract: Mapped["FinancialContract"] = relationship(
        "FinancialContract", back_populates="installments"
    )

    def __repr__(self) -> str:
        return f"<Installment id={self.id} number={self.number} status={self.status}>"
