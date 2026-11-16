from __future__ import annotations

import re
from typing import Any

from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.providers.google_client import GoogleClient
from mcp_workspace_common.providers.identifiers import _identifier
from pydantic import BaseModel

from mcp_google_docs.providers.content import (
    document_body,
    document_text,
    table_values,
    text_requests,
)
from mcp_google_docs.providers.verification import matches_document
from mcp_google_docs.schemas.create_document import CreateDocument
from mcp_google_docs.schemas.document_id import DocumentId
from mcp_google_docs.schemas.update_document import UpdateDocument

MIME = "application/vnd.google-apps.document"
BASE = "https://docs.googleapis.com/v1/documents/"
DRIVE = "https://www.googleapis.com/drive/v3/files"


class GoogleDocs:
    def __init__(self, transport: GoogleClient) -> None:
        self._request = transport.request

    async def _get(self, document_id: str) -> dict[str, Any]:
        return dict(
            await self._request(
                "GET",
                BASE + _identifier(document_id),
                read=True,
                params={"includeTabsContent": "true"},
            )
        )

    def _result(self, document: dict[str, Any]) -> dict[str, Any]:
        identifier = document.get("documentId", document.get("id", ""))
        title = document.get("title", document.get("name", identifier))
        url = f"https://docs.google.com/document/d/{identifier}/edit"
        return {
            "id": identifier,
            "title": title,
            "mime_type": MIME,
            "web_url": url,
            "revision_id": document.get("revisionId"),
            "document": document,
            "text": document_text(document),
            "sources": [
                {"provider": "docs", "resource_id": identifier, "title": title, "url": url}
            ],
            "verified": True,
        }

    async def snapshot(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if tool == "create_document":
            if not args.get("parent_id"):
                return {}
            return dict(
                await self._request(
                    "GET",
                    DRIVE + "/" + _identifier(args["parent_id"]),
                    read=True,
                    params={
                        "fields": "id,name,mimeType,version,capabilities(canAddChildren)",
                        "supportsAllDrives": "true",
                    },
                )
            )
        if tool != "update_document":
            return {}
        document = await self._get(args["document_id"])
        _, tab_id = document_body(document, args.get("tab_id"))
        if not document.get("revisionId"):
            raise ConnectorError("permission_denied", "An editable document revision is required")
        return {
            "document_id": args["document_id"],
            "title": document.get("title", ""),
            "revision_id": document["revisionId"],
            "tab_id": tab_id,
        }

    async def _batch(
        self, document_id: str, document: dict[str, Any], requests: list[dict[str, Any]]
    ) -> dict[str, Any]:
        revision = document.get("revisionId")
        if not revision:
            raise ConnectorError("permission_denied", "An editable document revision is required")
        reply = await self._request(
            "POST",
            BASE + document_id + ":batchUpdate",
            json={"requests": requests, "writeControl": {"requiredRevisionId": revision}},
        )
        refreshed = await self._get(document_id)
        written = reply.get("writeControl", {}).get("requiredRevisionId")
        if written and written != refreshed.get("revisionId"):
            raise ConnectorError("stale_action", "Document changed while applying approved edits")
        return refreshed

    async def _append(
        self,
        document_id: str,
        document: dict[str, Any],
        blocks: list[dict[str, Any]],
        tab_id: str | None,
    ) -> dict[str, Any]:
        pending: list[dict[str, Any]] = []
        for block in [*blocks, {"type": "_end"}]:
            if block["type"] not in {"table", "_end"}:
                pending.append(block)
                continue
            body, selected_tab = document_body(document, tab_id)
            end = max((item.get("endIndex", 1) for item in body.get("content", [])), default=2) - 1
            if pending:
                document = await self._batch(
                    document_id, document, text_requests(pending, max(1, end), selected_tab)
                )
                pending = []
            if block["type"] != "table":
                continue
            values = table_values(block)
            location = {"tabId": selected_tab} if selected_tab else {}
            document = await self._batch(
                document_id,
                document,
                [
                    {
                        "insertTable": {
                            "rows": len(values),
                            "columns": len(values[0]),
                            "endOfSegmentLocation": location,
                        }
                    }
                ],
            )
            body, _ = document_body(document, tab_id)
            tables = [item["table"] for item in body.get("content", []) if "table" in item]
            if not tables:
                raise ConnectorError(
                    "readback_failed", "The created document table could not be read back"
                )
            rows = tables[-1].get("tableRows", [])
            requests: list[dict[str, Any]] = []
            for row_number, row in enumerate(values):
                for column, text in enumerate(row):
                    cell = rows[row_number]["tableCells"][column]
                    index = cell["content"][0]["startIndex"]
                    target = {"index": index} | ({"tabId": selected_tab} if selected_tab else {})
                    if text:
                        requests.append({"insertText": {"location": target, "text": text}})
            requests.sort(
                key=lambda request: request["insertText"]["location"]["index"], reverse=True
            )
            if requests:
                document = await self._batch(document_id, document, requests)
        return document

    async def _create(self, args: dict[str, Any]) -> dict[str, Any]:
        parent = args.get("parent_id")
        if parent:
            snapshot = await self.snapshot("create_document", args)
            if (
                args.get("_snapshot") != snapshot
                or snapshot.get("mimeType") != "application/vnd.google-apps.folder"
            ):
                raise ConnectorError("stale_action", "Approved destination folder is required")
        operation = args.get("idempotency_key")
        if operation:
            _identifier(operation)
            existing = await self._request(
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
                result = self._result(await self._get(existing["files"][0]["id"]))
                if matches_document(result["document"], args["blocks"]):
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
        created = await self._request(
            "POST",
            DRIVE,
            params={"fields": "id,name,webViewLink", "supportsAllDrives": "true"},
            json=metadata,
        )
        document_id = created["id"]
        try:
            document = await self._get(document_id)
            if args["blocks"]:
                document = await self._append(document_id, document, args["blocks"], None)
            if not matches_document(document, args["blocks"]):
                raise ConnectorError(
                    "readback_failed", "Created document content did not match the approved content"
                )
            result = self._result(document)
            return result | {"status": "created", "operation_id": operation}
        except Exception:
            return {
                "id": document_id,
                "title": args["title"],
                "mime_type": MIME,
                "web_url": f"https://docs.google.com/document/d/{document_id}/edit",
                "status": "partial",
                "partial": True,
                "verified": False,
                "error_code": "PARTIAL_CREATION",
                "operation_id": operation,
            }

    async def call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        models: dict[str, type[BaseModel]] = {
            "get_document": DocumentId,
            "create_document": CreateDocument,
            "update_document": UpdateDocument,
        }
        if tool not in models:
            raise ConnectorError("unknown_tool", "Unknown Google Docs tool")
        clean = (
            models[tool]
            .model_validate(
                {
                    key: value
                    for key, value in args.items()
                    if not key.startswith("_") and key != "idempotency_key"
                }
            )
            .model_dump(mode="json")
        )
        args = clean | {
            key: value
            for key, value in args.items()
            if key.startswith("_") or key == "idempotency_key"
        }
        if tool == "get_document":
            document = await self._get(args["document_id"])
            document_body(document, args.get("tab_id"))
            return self._result(document)
        if tool == "create_document":
            return await self._create(args)
        approved = args.get("_snapshot")
        current = await self.snapshot(tool, args)
        if not approved or approved != current:
            raise ConnectorError("stale_action", "Document changed or approved revision is missing")
        document = await self._get(args["document_id"])
        if document.get("revisionId") != approved["revision_id"]:
            raise ConnectorError("stale_action", "Document changed after approval")
        expected_text = document_text(document_body(document, approved.get("tab_id"))[0])
        requests = []
        for change in args["replace_text"]:
            pattern = re.compile(
                re.escape(change["find"]), 0 if change["match_case"] else re.IGNORECASE
            )
            if not pattern.search(expected_text):
                raise ConnectorError(
                    "not_found", "The requested text was not found in the selected document tab"
                )
            replacement_text: str = change["replacement"]
            expected_text = pattern.sub(replacement_text.replace("\\", "\\\\"), expected_text)
            replacement = {
                "containsText": {"text": change["find"], "matchCase": change["match_case"]},
                "replaceText": change["replacement"],
            }
            if approved.get("tab_id"):
                replacement["tabsCriteria"] = {"tabIds": [approved["tab_id"]]}
            requests.append({"replaceAllText": replacement})
        if requests:
            document = await self._batch(args["document_id"], document, requests)
            actual_text = document_text(document_body(document, approved.get("tab_id"))[0])
            if actual_text != expected_text:
                raise ConnectorError(
                    "readback_failed",
                    "Approved text replacements could not be verified; inspect before retrying",
                )
        if args["append_blocks"]:
            document = await self._append(
                args["document_id"], document, args["append_blocks"], approved.get("tab_id")
            )
        if not matches_document(document, args["append_blocks"]):
            raise ConnectorError(
                "readback_failed",
                "Approved document content could not be verified; inspect before retrying",
            )
        return self._result(document) | {
            "status": "updated",
            "operation_id": args.get("idempotency_key"),
        }
