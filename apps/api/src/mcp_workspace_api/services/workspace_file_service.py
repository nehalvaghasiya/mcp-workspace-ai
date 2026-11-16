from __future__ import annotations

import base64
import binascii
import hashlib
import os
import re
import tempfile
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from sqlalchemy import select

from mcp_workspace_api.core.presenters import artifact_json, timestamp
from mcp_workspace_api.core.security import Denied
from mcp_workspace_api.db import Artifact, GoogleAccount, Run, User, now
from mcp_workspace_api.db.models.workspace_file import WorkspaceFile
from mcp_workspace_api.services.source_resolver import resolve_sources

if TYPE_CHECKING:
    from mcp_workspace_api.core.execution_context import Runtime

NATIVE_TYPES = {
    "docs": ("document", "application/vnd.google-apps.document"),
    "sheets": ("spreadsheets", "application/vnd.google-apps.spreadsheet"),
    "slides": ("presentation", "application/vnd.google-apps.presentation"),
}


def workspace_file_json(row: WorkspaceFile) -> dict[str, Any]:
    return {
        "id": row.id,
        "google_file_id": row.google_file_id,
        "kind": row.kind,
        "title": row.title,
        "mime_type": row.mime_type,
        "web_url": row.web_url,
        "revision": row.revision,
        "status": row.status,
        "artifact_id": row.artifact_id,
        "run_id": row.run_id,
        "created_at": timestamp(row.created_at),
        "updated_at": timestamp(row.updated_at),
    }


class WorkspaceFileService:
    def __init__(self, context: Runtime) -> None:
        self.context = context

    def record(
        self,
        user_id: str,
        run_id: str,
        server: str,
        result: dict[str, Any],
        arguments: dict[str, Any],
    ) -> WorkspaceFile | None:
        if server not in NATIVE_TYPES:
            return None
        file_id = next(
            (
                value
                for key in (
                    "id",
                    "document_id",
                    "spreadsheet_id",
                    "presentation_id",
                    "documentId",
                    "spreadsheetId",
                    "presentationId",
                )
                if isinstance(value := result.get(key), str)
            ),
            "",
        )
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", file_id):
            return None
        route, mime = NATIVE_TYPES[server]
        title = str(
            result.get("title") or result.get("name") or arguments.get("title") or "Untitled"
        )[:1000]
        with self.context.db.session() as session:
            user = session.get(User, user_id)
            if not user or user.deleted:
                return None
            if run_id:
                run = session.get(Run, run_id)
                if not run or run.user_id != user_id:
                    return None
            account = session.scalar(select(GoogleAccount).where(GoogleAccount.user_id == user_id))
            artifact_id = arguments.get("artifact_id")
            if artifact_id:
                artifact = session.get(Artifact, artifact_id)
                if not artifact or artifact.user_id != user_id:
                    artifact_id = None
            row = session.scalar(
                select(WorkspaceFile).where(
                    WorkspaceFile.user_id == user_id, WorkspaceFile.google_file_id == file_id
                )
            )
            if row is None:
                row = WorkspaceFile(user_id=user_id, google_file_id=file_id, kind=server)
                session.add(row)
            row.account_id = account.id if account else None
            row.run_id = run_id or None
            row.artifact_id = artifact_id or row.artifact_id
            row.title, row.mime_type = title, mime
            row.web_url = f"https://docs.google.com/{route}/d/{file_id}/edit"
            row.revision = str(result.get("revision_id") or result.get("revisionId") or "")[:1000]
            row.status = (
                "partial"
                if result.get("partial")
                else "ready"
                if result.get("verified")
                else "unverified"
            )
            row.updated_at = now()
            session.flush()
            return row

    def for_run(self, user_id: str, run_id: str) -> list[dict[str, Any]]:
        with self.context.db.session() as session:
            return [
                workspace_file_json(row)
                for row in session.scalars(
                    select(WorkspaceFile)
                    .where(WorkspaceFile.user_id == user_id, WorkspaceFile.run_id == run_id)
                    .order_by(WorkspaceFile.created_at)
                )
            ]

    def import_export(self, user_id: str, run_id: str, result: dict[str, Any]) -> dict[str, Any]:
        from mcp_documents.constants import EXTENSIONS, MIME_TYPES
        from mcp_documents.engine import ArtifactEngine

        # Export bytes never enter model context, event records, or API metadata.
        encoded = result.pop("content_base64", None)
        maximum = self.context.settings.max_artifact_bytes
        format_name = next(
            (name for name, mime in MIME_TYPES.items() if mime == result.get("mime_type")), None
        )
        if not format_name or not isinstance(encoded, str):
            raise Denied("UNSUPPORTED_FORMAT", "This Google export format is not supported")
        if len(encoded) > ((maximum + 2) // 3) * 4:
            raise Denied("QUOTA_EXCEEDED", "Export exceeds the configured file size limit")
        try:
            content = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError):
            raise Denied("INVALID_PROVIDER_RESPONSE", "Google export content is invalid") from None
        if not content or len(content) > maximum:
            raise Denied("QUOTA_EXCEEDED", "Export exceeds the configured file size limit")
        sources = [source.model_dump(mode="json") for source in resolve_sources("drive", result)]
        with self.context.db.session() as session:
            user = session.get(User, user_id)
            run = session.get(Run, run_id) if run_id else None
            if not user or user.deleted or (run_id and (not run or run.user_id != user_id)):
                raise Denied("PERMISSION_DENIED", "Export owner is unavailable")
        directory = self.context.settings.storage / "artifacts" / user_id
        if any(part.is_symlink() for part in (directory, *directory.parents)):
            raise Denied("PERMISSION_DENIED", "Artifact storage is unavailable")
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".google-export-", suffix=f".{EXTENSIONS[format_name]}", dir=directory
        )
        from pathlib import Path

        temporary = Path(temporary_name)
        destination = directory / f"{uuid4().hex}.{EXTENSIONS[format_name]}"
        stored = False
        try:
            with os.fdopen(descriptor, "wb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            ArtifactEngine(max_bytes=maximum).validate(temporary, format_name)
            with self.context.db.session() as session:
                user = session.get(User, user_id)
                if not user or user.deleted:
                    raise Denied("PERMISSION_DENIED", "Export owner is unavailable")
                existing = list(
                    session.scalars(select(Artifact).where(Artifact.user_id == user_id))
                )
                if (
                    len(existing) >= self.context.settings.max_user_artifacts
                    or sum(row.size for row in existing) + len(content)
                    > self.context.settings.max_user_artifact_bytes
                ):
                    raise Denied(
                        "QUOTA_EXCEEDED", "Artifact storage quota reached; remove old files first"
                    )
                temporary.replace(destination)
                artifact = Artifact(
                    user_id=user_id,
                    run_id=run_id or None,
                    title=str(result.get("name") or "Google export")[:1000],
                    format=format_name,
                    mime_type=MIME_TYPES[format_name],
                    size=len(content),
                    sha256=hashlib.sha256(content).hexdigest(),
                    storage_key=str(destination.relative_to(self.context.settings.storage)),
                    sources=sources,
                    validated=True,
                )
                session.add(artifact)
                session.flush()
                metadata = artifact_json(artifact)
            stored = True
            return metadata
        finally:
            temporary.unlink(missing_ok=True)
            if not stored:
                destination.unlink(missing_ok=True)
