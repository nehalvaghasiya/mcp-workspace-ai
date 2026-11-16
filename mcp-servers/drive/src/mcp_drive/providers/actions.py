from __future__ import annotations

import base64
from collections.abc import Awaitable, Callable
from typing import Any

from mcp_workspace_common.constants import FOLDER, GOOGLE_DOC, GOOGLE_SHEET, GOOGLE_SLIDES
from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.providers.google_client import GoogleClient
from mcp_workspace_common.providers.identifiers import _identifier
from mcp_workspace_common.utils.results import _source

BASE = "https://www.googleapis.com/drive/v3/files"
WRITES = {"copy_file", "rename_file", "move_file", "share_file", "trash_file"}
LIVE_TOOLS = {*WRITES, "list_drives", "export_file", "find_operation"}


class GoogleDriveActions:
    def __init__(
        self,
        transport: GoogleClient,
        metadata: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
    ) -> None:
        self._request = transport.request
        self.metadata = metadata

    async def call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if tool == "find_operation":
            from mcp_drive.schemas.find_operation import FindOperation

            operation = FindOperation.model_validate(
                {"operation_id": args["operation_id"]}
            ).operation_id
            result = await self._request(
                "GET",
                BASE,
                read=True,
                params={
                    "q": "trashed = false and appProperties has { key='workspace_operation' and value='"
                    + operation
                    + "' }",
                    "pageSize": 100,
                    "supportsAllDrives": "true",
                    "includeItemsFromAllDrives": "true",
                    "fields": "nextPageToken,files(id,name,mimeType,webViewLink,parents,appProperties)",
                },
            )
            return {
                "operation_id": operation,
                "files": result.get("files", []),
                "next_page_token": result.get("nextPageToken"),
                "sources": [_source("drive", item) for item in result.get("files", [])],
            }
        if tool == "list_drives":
            result = await self._request(
                "GET",
                "https://www.googleapis.com/drive/v3/drives",
                read=True,
                params={
                    "pageSize": min(int(args.get("max_results", 20)), 100),
                    "fields": "nextPageToken,drives(id,name,capabilities)",
                    **({"pageToken": args["page_token"]} if args.get("page_token") else {}),
                },
            )
            return {
                "drives": result.get("drives", []),
                "next_page_token": result.get("nextPageToken"),
            }
        if tool == "export_file":
            metadata = await self.metadata(args)
            if metadata.get("mimeType") not in {GOOGLE_DOC, GOOGLE_SHEET, GOOGLE_SLIDES}:
                raise ConnectorError(
                    "invalid_input",
                    "Only native Google documents, spreadsheets, and presentations can be exported",
                )
            if not metadata.get("capabilities", {}).get("canDownload", False):
                raise ConnectorError("permission_denied", "Exporting this file is not permitted")
            from mcp_drive.providers.resource_keys import _resource_headers

            content = await self._request(
                "GET",
                BASE + "/" + _identifier(args["file_id"]) + "/export",
                read=True,
                binary=True,
                headers=_resource_headers(args),
                params={"mimeType": args.get("mime_type", "application/pdf")},
            )
            return {
                "id": metadata["id"],
                "name": metadata.get("name", "Export"),
                "mime_type": args.get("mime_type", "application/pdf"),
                "size": len(content),
                "content_base64": base64.b64encode(content).decode(),
                "sources": [_source("drive", metadata)],
            }
        if tool not in WRITES:
            raise ConnectorError("unknown_tool", "Unknown Drive tool")
        approved = args.get("_snapshot")
        if not approved:
            raise ConnectorError("stale_action", "Approved Drive snapshot is required")
        if await self.snapshot(tool, args) != approved:
            raise ConnectorError("stale_action", "Drive file or destination changed after approval")
        target = BASE + "/" + _identifier(args["file_id"])
        params: dict[str, Any] = {"supportsAllDrives": "true"}
        if tool == "share_file":
            result = await self._request(
                "POST",
                target + "/permissions",
                json={
                    "type": "user",
                    "emailAddress": args["email"],
                    "role": args.get("role", "reader"),
                },
                params=params
                | {
                    "sendNotificationEmail": "true"
                    if args.get("send_notification", True)
                    else "false",
                    "fields": "id,type,emailAddress,role",
                },
            )
            permission_id = result.get("id")
            if not permission_id:
                raise ConnectorError(
                    "outcome_unknown",
                    "Sharing outcome is unknown; inspect file permissions before retrying",
                )
            verified = await self._request(
                "GET",
                target + "/permissions/" + _identifier(permission_id),
                read=True,
                params=params | {"fields": "id,type,emailAddress,role"},
            )
            if (
                verified.get("role") != args.get("role", "reader")
                or str(verified.get("emailAddress", "")).casefold() != str(args["email"]).casefold()
            ):
                raise ConnectorError(
                    "outcome_unknown",
                    "Sharing readback did not match the approved recipient and role",
                )
            return {"id": args["file_id"], "permission": verified, "readback_verified": True}
        if tool == "copy_file":
            body: dict[str, Any] = {"name": args["name"]}
            if args.get("folder_id"):
                body["parents"] = [args["folder_id"]]
            if args.get("idempotency_key"):
                body["appProperties"] = {"workspace_operation": args["idempotency_key"]}
            result = await self._request(
                "POST",
                target + "/copy",
                json=body,
                params=params | {"fields": "id,name,mimeType,parents,webViewLink,version"},
            )
            if not result.get("id"):
                raise ConnectorError(
                    "outcome_unknown", "File copy outcome is unknown; inspect Drive before retrying"
                )
            verified = await self.metadata({"file_id": result["id"]})
            return verified | {"readback_verified": True}
        changes: dict[str, Any] = {}
        if tool == "rename_file":
            changes["name"] = args["name"]
        elif tool == "trash_file":
            changes["trashed"] = True
        elif tool == "move_file":
            params["addParents"] = args["folder_id"]
            old_parents = approved["file"].get("parents", [])
            if old_parents:
                params["removeParents"] = ",".join(old_parents)
        await self._request(
            "PATCH",
            target,
            json=changes,
            params=params | {"fields": "id,name,parents,trashed,version"},
        )
        verified = await self.metadata(args)
        if (
            (tool == "rename_file" and verified.get("name") != args["name"])
            or (tool == "trash_file" and not verified.get("trashed"))
            or (tool == "move_file" and args["folder_id"] not in verified.get("parents", []))
        ):
            raise ConnectorError(
                "outcome_unknown",
                "Drive change could not be verified; inspect the file before retrying",
            )
        return verified | {"readback_verified": True}

    async def snapshot(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if tool not in WRITES:
            return {}
        result: dict[str, Any] = {"file": await self.metadata(args)}
        if args.get("folder_id"):
            destination = await self.metadata({"file_id": args["folder_id"]})
            if destination.get("mimeType") != FOLDER:
                raise ConnectorError("invalid_input", "The destination must be a Drive folder")
            result["destination"] = destination
        if tool == "share_file":
            permissions = await self._request(
                "GET",
                BASE + "/" + _identifier(args["file_id"]) + "/permissions",
                read=True,
                params={
                    "supportsAllDrives": "true",
                    "pageSize": 100,
                    "fields": "nextPageToken,permissions(id,type,emailAddress,role)",
                },
            )
            if permissions.get("nextPageToken"):
                raise ConnectorError(
                    "limit_exceeded",
                    "This file has too many permissions for a bounded approval preview",
                )
            result["permissions"] = sorted(
                permissions.get("permissions", []), key=lambda item: item.get("id", "")
            )
        return result
