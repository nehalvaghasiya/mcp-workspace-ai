from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from mcp_workspace_api.db.models.base import Base
from mcp_workspace_api.db.models.owned import Owned


class RunEvent(Owned, Base):
    __tablename__ = "run_events"
    sequence: Mapped[int] = mapped_column(primary_key=False, index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), index=True)
    type: Mapped[str]
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
