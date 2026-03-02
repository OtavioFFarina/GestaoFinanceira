"""
AIMessage model — individual messages within a conversation.
Stores sources/citations in JSONB to enable transparency and anti-hallucination auditing.
"""
import enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.ai_conversation import AIConversation


class MessageRoleEnum(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AIMessage(Base, TimestampMixin):
    __tablename__ = "ai_messages"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRoleEnum] = mapped_column(
        SAEnum(MessageRoleEnum, name="message_role_enum"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Sources cited by the agent — stored for auditing and anti-hallucination tracking.
    # Example: [{"url": "...", "title": "...", "date": "2024-03-01", "source": "BCB"}]
    sources: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSONB, nullable=True)

    # Relationships
    conversation: Mapped["AIConversation"] = relationship(
        "AIConversation", back_populates="messages"
    )

    def __repr__(self) -> str:
        return f"<AIMessage id={self.id} role={self.role}>"
