from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from mcp_workspace_api.db.models.base import Base


class OAuthState(Base):
    __tablename__ = "oauth_states"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    browser_hash: Mapped[str]
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    nonce: Mapped[str]
    verifier: Mapped[str]
    connector: Mapped[str]
    expires_at: Mapped[float]
