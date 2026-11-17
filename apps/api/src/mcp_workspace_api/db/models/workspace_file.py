from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from mcp_workspace_api.db.models.base import Base
from mcp_workspace_api.db.models.owned import Owned
from mcp_workspace_api.db.utils import now


class WorkspaceFile(Owned, Base):
    __tablename__ = "workspace_files"
    __table_args__ = (
        UniqueConstraint("user_id", "google_file_id", name="uq_workspace_file_owner"),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[str | None] = mapped_column(
        ForeignKey("google_accounts.id", ondelete="SET NULL"), nullable=True
    )
    run_id: Mapped[str | None] = mapped_column(
        ForeignKey("runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    artifact_id: Mapped[str | None] = mapped_column(
        ForeignKey("artifacts.id", ondelete="SET NULL"), nullable=True
    )
    google_file_id: Mapped[str] = mapped_column(String(256))
    kind: Mapped[str] = mapped_column(String(16))
    title: Mapped[str]
    mime_type: Mapped[str]
    web_url: Mapped[str]
    revision: Mapped[str] = mapped_column(default="")
    status: Mapped[str] = mapped_column(String(16), default="unverified")
    updated_at: Mapped[float] = mapped_column(default=now)
