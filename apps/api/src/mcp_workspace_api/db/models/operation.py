from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from mcp_workspace_api.db.models.base import Base
from mcp_workspace_api.db.models.owned import Owned


class Operation(Owned, Base):
    __tablename__ = "operations"
    approval_id: Mapped[str] = mapped_column(ForeignKey("approvals.id"), unique=True)
    status: Mapped[str] = mapped_column(default="dispatched")
    result: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
