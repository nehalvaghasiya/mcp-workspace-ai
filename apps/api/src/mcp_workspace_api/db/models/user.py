from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from mcp_workspace_api.db.models.base import Base
from mcp_workspace_api.db.utils import uid


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    subject: Mapped[str] = mapped_column(String(256), unique=True)
    display_name: Mapped[str] = mapped_column(default="Demo explorer")
    email: Mapped[str] = mapped_column(default="")
    timezone: Mapped[str] = mapped_column(default="America/Chicago")
    llm_consent: Mapped[bool] = mapped_column(default=False)
    consent_provider: Mapped[str] = mapped_column(default="")
    deleted: Mapped[bool] = mapped_column(default=False)
