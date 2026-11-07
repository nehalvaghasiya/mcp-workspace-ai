from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from mcp_workspace_api.core.presenters import artifact_json
from mcp_workspace_api.core.security import Denied
from mcp_workspace_api.db import (
    Artifact,
    User,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.execution_context import Runtime


class ArtifactService:
    def __init__(self, context: Runtime) -> None:
        self.context = context

    async def _artifact(
        self, user_id: str, run_id: str, leaf: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        context = self.context
        from mcp_documents.artifacts import ArtifactEngine, ArtifactSpec

        if leaf.startswith("create_"):
            if args["format"] != leaf.removeprefix("create_"):
                raise Denied("INVALID_ARGUMENT", "Artifact format must match the selected tool")
            spec = ArtifactSpec.model_validate(args)
            with context.db.session() as session:
                existing = list(
                    session.scalars(select(Artifact).where(Artifact.user_id == user_id))
                )
                if len(existing) >= context.settings.max_user_artifacts:
                    raise Denied(
                        "QUOTA_EXCEEDED", "Artifact count quota reached; remove old files first"
                    )
            async with context.render_slots:
                rendering = asyncio.create_task(
                    asyncio.to_thread(
                        ArtifactEngine(max_bytes=context.settings.max_artifact_bytes).create,
                        spec,
                        context.settings.storage / "artifacts" / user_id,
                    )
                )
                try:
                    rendered = await asyncio.shield(rendering)
                except asyncio.CancelledError:
                    rendered = await rendering
                    rendered.path.unlink(missing_ok=True)
                    raise
            with context.db.session() as session:
                user = session.get(User, user_id)
                if not user or user.deleted:
                    rendered.path.unlink(missing_ok=True)
                    raise Denied("PERMISSION_DENIED", "User data was deleted")
                existing = list(
                    session.scalars(select(Artifact).where(Artifact.user_id == user_id))
                )
                if (
                    len(existing) >= context.settings.max_user_artifacts
                    or sum(row.size for row in existing) + rendered.size
                    > context.settings.max_user_artifact_bytes
                ):
                    rendered.path.unlink(missing_ok=True)
                    raise Denied(
                        "QUOTA_EXCEEDED", "Artifact storage quota reached; remove old files first"
                    )
                artifact = Artifact(
                    user_id=user_id,
                    run_id=run_id or None,
                    title=spec.title,
                    format=rendered.format,
                    mime_type=rendered.mime_type,
                    size=rendered.size,
                    sha256=rendered.sha256,
                    storage_key=str(rendered.path.relative_to(context.settings.storage)),
                    sources=[],
                )
                session.add(artifact)
                session.flush()
                return artifact_json(artifact)
        with context.db.session() as session:
            if leaf == "list_artifacts":
                return {
                    "artifacts": [
                        artifact_json(row)
                        for row in session.scalars(
                            select(Artifact)
                            .where(Artifact.user_id == user_id)
                            .limit(args["max_results"])
                        )
                    ]
                }
            stored_artifact = session.get(Artifact, args["artifact_id"])
            if not stored_artifact or stored_artifact.user_id != user_id:
                raise Denied("RESOURCE_NOT_FOUND", "Artifact is unavailable")
            result = artifact_json(stored_artifact)
            if leaf == "validate_artifact":
                result["validation"] = ArtifactEngine().validate(
                    context.settings.storage / stored_artifact.storage_key, stored_artifact.format
                )
            return result
