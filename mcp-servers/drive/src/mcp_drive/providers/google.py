from __future__ import annotations

import json
import re
import uuid
from typing import Any

from mcp_workspace_common.constants import EXPORTS, FOLDER
from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.extraction import MAX_FILE_BYTES, ExtractionError, extract_text
from mcp_workspace_common.providers.google_client import GoogleClient
from mcp_workspace_common.providers.identifiers import _identifier
from mcp_workspace_common.utils.artifacts import _artifact_bytes
from mcp_workspace_common.utils.results import _source

from mcp_drive.providers.actions import LIVE_TOOLS, GoogleDriveActions
from mcp_drive.providers.resource_keys import _resource_headers


class GoogleDrive:
    def __init__(self, transport: GoogleClient) -> None:
        self._request = transport.request
        self.actions = GoogleDriveActions(transport, self._metadata)

    async def _metadata(self, args: dict[str, Any]) -> dict[str, Any]:
        return await self.call("get_file_metadata", args)

    async def call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        base = "https://www.googleapis.com/drive/v3/files"
        fields = "id,name,mimeType,parents,webViewLink,modifiedTime,size,version,driveId,capabilities(canDownload,canEdit,canShare,canTrash,canAddChildren),trashed"
        if tool in LIVE_TOOLS:
            return await self.actions.call(tool, args)
        if tool in {"search_files", "list_folder"}:
            query = args.get("query", "")
            clauses = ["trashed = false"]
            if query:
                if re.match(r"^(?:name|fullText|mimeType|trashed)\s|^'", query):
                    clauses.append(f"({query})")
                else:
                    escaped = str(query).replace("\\", "\\\\").replace("'", "\\'")
                    clauses.append(f"fullText contains '{escaped}'")
            parent = args.get("folder_id") if tool == "list_folder" else args.get("parent_id")
            if parent:
                _identifier(parent)
                clauses.append("'" + str(parent).replace("'", "\\'") + "' in parents")
            if args.get("mime_types"):
                clauses.append(
                    "("
                    + " or ".join(
                        "mimeType = '" + str(m).replace("'", "\\'") + "'"
                        for m in args["mime_types"]
                    )
                    + ")"
                )
            params = {
                "q": " and ".join(clauses),
                "pageSize": min(int(args.get("max_results", 20)), 100),
                "fields": f"nextPageToken,incompleteSearch,files({fields})",
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
                "corpora": "user",
            }
            if args.get("drive_id"):
                params["corpora"] = "drive"
                params["driveId"] = _identifier(args["drive_id"])
            if args.get("page_token"):
                params["pageToken"] = args["page_token"]
            result = await self._request("GET", base, read=True, params=params)
            return {
                "files": result.get("files", []),
                "next_page_token": result.get("nextPageToken"),
                "incomplete_search": bool(result.get("incompleteSearch", False)),
                "scope_note": "Results include files accessible with the account's granted Drive permissions",
                "sources": [_source("drive", x) for x in result.get("files", [])],
            }
        if tool in {"get_file_metadata", "read_file"}:
            url = base + "/" + _identifier(args["file_id"])
            headers = _resource_headers(args)
            metadata = await self._request(
                "GET",
                url,
                read=True,
                headers=headers,
                params={"fields": fields, "supportsAllDrives": "true"},
            )
            if tool == "get_file_metadata":
                return metadata
            if not metadata.get("capabilities", {}).get("canDownload", False):
                raise ConnectorError("permission_denied", "Downloading this file is not permitted")
            mime = metadata["mimeType"]
            if mime in EXPORTS:
                mime = EXPORTS[mime]
                content = await self._request(
                    "GET",
                    url + "/export",
                    read=True,
                    binary=True,
                    headers=headers,
                    params={"mimeType": mime},
                )
            else:
                if int(metadata.get("size", 0)) > MAX_FILE_BYTES:
                    raise ConnectorError("file_too_large", "File exceeds 10 MiB extraction limit")
                content = await self._request(
                    "GET", url, read=True, binary=True, headers=headers, params={"alt": "media"}
                )
            try:
                result = extract_text(content, mime, int(args.get("max_chars", 20000)))
            except ExtractionError as exc:
                raise ConnectorError("extraction_failed", str(exc)) from None
            return result | {
                "id": metadata["id"],
                "name": metadata["name"],
                "sources": [_source("drive", metadata)],
            }
        if tool == "create_folder":
            body = {"name": args["name"], "mimeType": FOLDER}
            if args.get("parent_id"):
                body["parents"] = [args["parent_id"]]
                if args.get("idempotency_key") and await self.snapshot(tool, args) != args.get(
                    "_snapshot"
                ):
                    raise ConnectorError(
                        "stale_action", "Destination folder changed after approval"
                    )
            if args.get("idempotency_key"):
                body["appProperties"] = {"workspace_operation": args["idempotency_key"]}
            created = await self._request(
                "POST", base, json=body, params={"fields": fields, "supportsAllDrives": "true"}
            )
            if args.get("idempotency_key"):
                created = await self._created_readback(
                    created, args["name"], FOLDER, args.get("parent_id")
                )
            return created
        if tool == "upload_artifact":
            artifact = args.get("_artifact")
            if not artifact:
                raise ConnectorError("artifact_unavailable", "Verified owned artifact required")
            data = _artifact_bytes(artifact)
            metadata = {"name": args.get("target_name") or artifact["title"]}
            if args.get("idempotency_key"):
                metadata["appProperties"] = {"workspace_operation": args["idempotency_key"]}
            if args.get("folder_id"):
                current = await self.snapshot(tool, args)
                if current.get("mimeType") != FOLDER or args.get("_snapshot") != current:
                    raise ConnectorError(
                        "stale_action", "Destination folder changed or approved snapshot is missing"
                    )
                metadata["parents"] = [args["folder_id"]]
            conversion = args.get("convert_to_google_type")
            if conversion:
                if conversion not in EXPORTS:
                    raise ConnectorError("invalid_input", "Unsupported Google conversion target")
                metadata["mimeType"] = conversion
            boundary = "workspace_" + uuid.uuid4().hex
            payload = (
                f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode()
                + json.dumps(metadata).encode()
                + f"\r\n--{boundary}\r\nContent-Type: {artifact['mime_type']}\r\n\r\n".encode()
                + data
                + f"\r\n--{boundary}--\r\n".encode()
            )
            uploaded = await self._request(
                "POST",
                "https://www.googleapis.com/upload/drive/v3/files",
                params={"uploadType": "multipart", "fields": fields, "supportsAllDrives": "true"},
                headers={"Content-Type": f"multipart/related; boundary={boundary}"},
                content=payload,
            )
            if args.get("idempotency_key"):
                uploaded = await self._created_readback(
                    uploaded,
                    str(metadata["name"]),
                    str(conversion or artifact["mime_type"]),
                    args.get("folder_id"),
                )
            return uploaded
        raise ConnectorError("unknown_tool", "Unknown Drive tool")

    async def snapshot(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if tool in LIVE_TOOLS:
            return await self.actions.snapshot(tool, args)
        if tool == "create_folder" and args.get("parent_id"):
            parent = await self.call("get_file_metadata", {"file_id": args["parent_id"]})
            if parent.get("mimeType") != FOLDER:
                raise ConnectorError("invalid_input", "Destination must be a Drive folder")
            return parent
        return (
            await self.call("get_file_metadata", {"file_id": args["folder_id"]})
            if args.get("folder_id")
            else {}
        )

    async def _created_readback(
        self, response: dict[str, Any], name: str, mime_type: str, parent_id: str | None
    ) -> dict[str, Any]:
        if not response.get("id"):
            raise ConnectorError(
                "outcome_unknown", "Drive creation returned no ID; inspect Drive before retrying"
            )
        current = await self.call("get_file_metadata", {"file_id": response["id"]})
        if (
            current.get("name") != name
            or current.get("mimeType") != mime_type
            or (parent_id and parent_id not in current.get("parents", []))
        ):
            raise ConnectorError(
                "outcome_unknown",
                "Drive readback differs from the approved file; inspect it before retrying",
            )
        return current | {"readback_verified": True}
