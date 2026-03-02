"""
User model — stores authentication and profile data.
SOLID: Single Responsibility → handles only user identity concerns.
"""
from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.monthly_record import MonthlyRecord
    from app.models.allocation_profile import AllocationProfile
    from app.models.ai_conversation import AIConversation


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    monthly_records: Mapped[List["MonthlyRecord"]] = relationship(
        "MonthlyRecord", back_populates="user", cascade="all, delete-orphan"
    )
    allocation_profiles: Mapped[List["AllocationProfile"]] = relationship(
        "AllocationProfile", back_populates="user", cascade="all, delete-orphan"
    )
    ai_conversations: Mapped[List["AIConversation"]] = relationship(
        "AIConversation", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
