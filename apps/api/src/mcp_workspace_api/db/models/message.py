from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from mcp_workspace_api.db.models.base import Base
from mcp_workspace_api.db.models.owned import Owned


class Message(Owned, Base):
    __tablename__ = "messages"
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str]
    content: Mapped[str]
    sources: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    artifacts: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
