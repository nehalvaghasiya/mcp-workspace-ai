from __future__ import annotations

import hashlib
from typing import Any
from uuid import uuid4

from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.providers.identifiers import _identifier

from mcp_slides.providers.content import slide_requests
from mcp_slides.providers.verification import matches_presentation

DRIVE = "https://www.googleapis.com/drive/v3/files"
MIME = "application/vnd.google-apps.presentation"


async def create_presentation(provider: Any, args: dict[str, Any]) -> dict[str, Any]:
    parent = args.get("parent_id")
    if parent:
        snapshot = await provider.snapshot("create_presentation", args)
        if (
            args.get("_snapshot") != snapshot
            or snapshot.get("mimeType") != "application/vnd.google-apps.folder"
        ):
            raise ConnectorError("stale_action", "Approved destination folder is required")
    operation = args.get("idempotency_key")
    if operation:
        _identifier(operation)
        existing = await provider._request(
            "GET",
            DRIVE,
            read=True,
            params={
                "q": f"trashed = false and appProperties has {{ key='workspace_operation' and value='{operation}' }}",
                "fields": "files(id,name)",
                "pageSize": 2,
            },
        )
        if existing.get("files"):
            presentation = await provider._get(existing["files"][0]["id"])
            result = provider._result(presentation)
            if matches_presentation(presentation, args["slides"]):
                return result | {"status": "reconciled", "operation_id": operation}
            return result | {
                "status": "partial",
                "partial": True,
                "verified": False,
                "error_code": "PARTIAL_CREATION",
                "operation_id": operation,
            }
    metadata: dict[str, Any] = {"name": args["title"], "mimeType": MIME}
    if parent:
        metadata["parents"] = [parent]
    if operation:
        metadata["appProperties"] = {"workspace_operation": operation}
    created = await provider._request(
        "POST",
        DRIVE,
        params={"fields": "id,name,webViewLink", "supportsAllDrives": "true"},
        json=metadata,
    )
    identifier = created["id"]
    try:
        presentation = await provider._get(identifier)
        prefix = "ws_" + hashlib.sha256(str(operation or uuid4().hex).encode()).hexdigest()[:16]
        requests, notes = slide_requests(args["slides"], prefix)
        presentation = await provider._batch(identifier, presentation, requests)
        presentation = await provider._notes(identifier, presentation, notes)
        if not matches_presentation(presentation, args["slides"]):
            raise ConnectorError(
                "readback_failed", "Created presentation content could not be verified"
            )
        return provider._result(presentation) | {"status": "created", "operation_id": operation}
    except Exception:
        return {
            "id": identifier,
            "title": args["title"],
            "mime_type": MIME,
            "web_url": f"https://docs.google.com/presentation/d/{identifier}/edit",
            "status": "partial",
            "partial": True,
            "verified": False,
            "error_code": "PARTIAL_CREATION",
            "operation_id": operation,
        }
