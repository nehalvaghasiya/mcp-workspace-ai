from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from mcp_workspace_api.db import (
    Approval,
    Artifact,
    now,
)


def timestamp(value: float | None = None) -> str:
    return datetime.fromtimestamp(value or now(), UTC).isoformat()


def artifact_json(artifact: Artifact) -> dict[str, Any]:
    return {
        "id": artifact.id,
        "title": artifact.title,
        "format": artifact.format,
        "mime_type": artifact.mime_type,
        "size": artifact.size,
        "sha256": artifact.sha256,
        "created_at": timestamp(artifact.created_at),
        "validated": artifact.validated,
        "sources": artifact.sources,
        "download_url": f"/api/artifacts/{artifact.id}/download",
    }


def approval_json(approval: Approval) -> dict[str, Any]:
    preview = {
        key: value
        for key, value in approval.snapshot.items()
        if key not in {"raw", "content", "body_html"}
    }
    return {
        "id": approval.id,
        "run_id": approval.run_id,
        "tool": approval.tool,
        "arguments": approval.arguments,
        "summary": {**preview, **approval.arguments},
        "status": approval.status,
        "expires_at": timestamp(approval.expires_at),
        "action_digest": approval.action_digest,
    }
