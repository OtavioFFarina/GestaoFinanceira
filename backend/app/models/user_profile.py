"""
UserProfile model — stores display preferences (theme, display name, photo).
"""
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.user import User


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    theme: Mapped[str] = mapped_column(String(10), nullable=False, default="dark")
    history_months: Mapped[int] = mapped_column(Integer, nullable=False, default=12)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="profile", uselist=False)

    def __repr__(self) -> str:
        return f"<UserProfile id={self.id} user_id={self.user_id}>"
