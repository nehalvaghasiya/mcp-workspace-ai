from __future__ import annotations

from sqlalchemy import JSON, String
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
