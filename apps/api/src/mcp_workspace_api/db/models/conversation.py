from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column

from mcp_workspace_api.db.models.base import Base
from mcp_workspace_api.db.models.owned import Owned
from mcp_workspace_api.db.utils import now


class Conversation(Owned, Base):
    __tablename__ = "conversations"
    title: Mapped[str] = mapped_column(default="New conversation")
    updated_at: Mapped[float] = mapped_column(default=now)
