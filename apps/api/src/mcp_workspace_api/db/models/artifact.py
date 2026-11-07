from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from mcp_workspace_api.db.models.base import Base
from mcp_workspace_api.db.models.owned import Owned


class Artifact(Owned, Base):
    __tablename__ = "artifacts"
    run_id: Mapped[str | None] = mapped_column(ForeignKey("runs.id"), nullable=True)
    title: Mapped[str]
    format: Mapped[str]
    mime_type: Mapped[str]
    storage_key: Mapped[str]
    size: Mapped[int]
    sha256: Mapped[str]
    validated: Mapped[bool] = mapped_column(default=True)
    sources: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
