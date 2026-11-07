from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select

from mcp_workspace_api.core.execution_context import (
    artifact_json,
)
from mcp_workspace_api.db import (
    Artifact,
    User,
)
from mcp_workspace_api.db.repositories.ownership import owned
from mcp_workspace_api.schemas.responses import (
    ArtifactView,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


def register(app: FastAPI, context: ApplicationContext) -> None:
    settings = context.settings
    db = context.db
    app = context.app
    require_user = context.session_service.require_user

    @app.get("/api/artifacts", response_model=list[ArtifactView])
    async def artifacts(user: User = Depends(require_user)) -> list[dict[str, Any]]:
        with db.session() as session:
            return [
                artifact_json(row)
                for row in session.scalars(
                    select(Artifact)
                    .where(Artifact.user_id == user.id)
                    .order_by(Artifact.created_at.desc())
                    .limit(100)
                )
            ]

    @app.get("/api/artifacts/{artifact_id}", response_model=ArtifactView)
    async def artifact_metadata(
        artifact_id: str, user: User = Depends(require_user)
    ) -> dict[str, Any]:
        with db.session() as session:
            return artifact_json(owned(session, Artifact, artifact_id, user))

    @app.get("/api/artifacts/{artifact_id}/download")
    async def download(artifact_id: str, user: User = Depends(require_user)) -> FileResponse:
        with db.session() as session:
            row = owned(session, Artifact, artifact_id, user)
        path = (settings.storage / row.storage_key).resolve()
        if not path.is_relative_to(settings.storage / "artifacts" / user.id) or not path.is_file():
            raise HTTPException(404, "File is unavailable")
        # HTML is downloaded, never served as active same-origin document content.
        return FileResponse(
            path,
            media_type=row.mime_type,
            filename=f"report-{row.id[:8]}.{path.suffix.lstrip('.')}",
            content_disposition_type="attachment",
        )

    @app.delete("/api/artifacts/{artifact_id}")
    async def delete_artifact(
        artifact_id: str, user: User = Depends(require_user)
    ) -> dict[str, str]:
        with db.session() as session:
            row = owned(session, Artifact, artifact_id, user)
            (settings.storage / row.storage_key).unlink(missing_ok=True)
            session.delete(row)
        return {"status": "deleted"}
