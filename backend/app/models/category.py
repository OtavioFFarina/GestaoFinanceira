"""
Category model — transaction categories (e.g. moradia, lazer, investimentos).
"""
import enum
from typing import Optional

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, generate_uuid


class CategoryTypeEnum(str, enum.Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"
    TRANSFERENCIA = "transferencia"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # NULL = global/system category
        index=True,
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hex_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    type: Mapped[CategoryTypeEnum] = mapped_column(
        SAEnum(CategoryTypeEnum, name="category_type_enum"),
        nullable=False,
        default=CategoryTypeEnum.SAIDA,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Category id={self.id} slug={self.slug} type={self.type}>"
