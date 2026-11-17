from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from fastapi import Depends, FastAPI, Query
from sqlalchemy import select

from mcp_workspace_api.db import User
from mcp_workspace_api.db.models.workspace_file import WorkspaceFile
from mcp_workspace_api.db.repositories.ownership import owned
from mcp_workspace_api.schemas.responses.workspace_file_view import WorkspaceFileView
from mcp_workspace_api.services.workspace_file_service import workspace_file_json

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


def register(app: FastAPI, context: ApplicationContext) -> None:
    require_user = context.session_service.require_user

    @app.get("/api/workspace-files", response_model=list[WorkspaceFileView])
    async def workspace_files(
        kind: Literal["docs", "sheets", "slides"] | None = None,
        limit: int = Query(default=100, ge=1, le=100),
        offset: int = Query(default=0, ge=0, le=10000),
        user: User = Depends(require_user),
    ) -> list[dict[str, Any]]:
        statement = select(WorkspaceFile).where(WorkspaceFile.user_id == user.id)
        if kind:
            statement = statement.where(WorkspaceFile.kind == kind)
        with context.db.session() as session:
            return [
                workspace_file_json(row)
                for row in session.scalars(
                    statement.order_by(WorkspaceFile.updated_at.desc()).limit(limit).offset(offset)
                )
            ]

    @app.get("/api/workspace-files/{file_id}", response_model=WorkspaceFileView)
    async def workspace_file(file_id: str, user: User = Depends(require_user)) -> dict[str, Any]:
        with context.db.session() as session:
            return workspace_file_json(owned(session, WorkspaceFile, file_id, user))
