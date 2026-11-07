from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from mcp_workspace_api.db.models.base import Base
from mcp_workspace_api.db.models.owned import Owned


class Approval(Owned, Base):
    __tablename__ = "approvals"
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), index=True)
    tool: Mapped[str]
    arguments: Mapped[dict[str, Any]] = mapped_column(JSON)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    action_digest: Mapped[str]
    account_id: Mapped[str]
    expires_at: Mapped[float]
    status: Mapped[str] = mapped_column(default="pending")
    capability_hash: Mapped[str] = mapped_column(default="")
