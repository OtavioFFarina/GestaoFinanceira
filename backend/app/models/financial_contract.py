"""
FinancialContract model — accounts payable and receivable contracts.
"""
import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Date, DateTime, Enum as SAEnum, ForeignKey, Integer,
    Numeric, String, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_uuid

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.installment import Installment


class ContractTypeEnum(str, enum.Enum):
    PAGAR = "pagar"
    RECEBER = "receber"


class ContractStatusEnum(str, enum.Enum):
    ATIVO = "ativo"
    QUITADO = "quitado"
    CANCELADO = "cancelado"


class FinancialContract(Base):
    __tablename__ = "financial_contracts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[ContractTypeEnum] = mapped_column(
        SAEnum(ContractTypeEnum, name="contract_type_enum"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    num_installments: Mapped[int] = mapped_column(Integer, nullable=False)
    first_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ContractStatusEnum] = mapped_column(
        SAEnum(ContractStatusEnum, name="contract_status_enum"),
        nullable=False,
        default=ContractStatusEnum.ATIVO,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="financial_contracts")
    installments: Mapped[List["Installment"]] = relationship(
        "Installment", back_populates="contract",
        cascade="all, delete-orphan",
        order_by="Installment.number",
    )

    def __repr__(self) -> str:
        return f"<FinancialContract id={self.id} type={self.type} status={self.status}>"
