from __future__ import annotations

from sqlalchemy import JSON, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from mcp_workspace_api.db.models.base import Base
from mcp_workspace_api.db.models.owned import Owned


class GoogleAccount(Owned, Base):
    __tablename__ = "google_accounts"
    subject: Mapped[str]
    credentials: Mapped[str]
    key_version: Mapped[str] = mapped_column(String(64), default="v1", server_default="v1")
    scopes: Mapped[list[str]] = mapped_column(JSON, default=list)
    enabled: Mapped[list[str]] = mapped_column(JSON, default=lambda: ["gmail", "calendar", "drive"])
    connection_error: Mapped[str] = mapped_column(String(64), default="", server_default="")
    connection_checked_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    connector_errors: Mapped[dict[str, str]] = mapped_column(
        JSON, default=dict, server_default="{}"
    )
