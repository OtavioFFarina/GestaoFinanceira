"""
Goal model — financial savings goals (e.g. 'Reserva de Emergência', 'Viagem').
"""
import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date, DateTime, Enum as SAEnum, ForeignKey, Numeric,
    String, Text, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, generate_uuid

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category


class GoalStatusEnum(str, enum.Enum):
    ATIVA = "ativa"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    current_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)
    deadline: Mapped[date] = mapped_column(Date, nullable=False)
    category_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[GoalStatusEnum] = mapped_column(
        SAEnum(GoalStatusEnum, name="goal_status_enum"),
        nullable=False,
        default=GoalStatusEnum.ATIVA,
    )
    ai_tips: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="goals")
    category: Mapped[Optional["Category"]] = relationship("Category", lazy="joined")

    @property
    def progress_pct(self) -> float:
        if self.target_amount and float(self.target_amount) > 0:
            return round(float(self.current_amount) / float(self.target_amount) * 100, 2)
        return 0.0

    def __repr__(self) -> str:
        return f"<Goal id={self.id} title={self.title} status={self.status}>"
