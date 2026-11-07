from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from mcp_workspace_api.db.models.base import Base
from mcp_workspace_api.db.models.owned import Owned


class Run(Owned, Base):
    __tablename__ = "runs"
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    request_id: Mapped[str] = mapped_column(String(200), unique=True)
    prompt: Mapped[str]
    status: Mapped[str] = mapped_column(default="queued", index=True)
    state: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error: Mapped[str] = mapped_column(default="")
