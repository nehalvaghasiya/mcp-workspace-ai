from __future__ import annotations

from typing import Any

from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.providers.identifiers import _identifier

from mcp_sheets.providers.mutations import update_cells
from mcp_sheets.providers.verification import matches_created

DRIVE = "https://www.googleapis.com/drive/v3/files"
MIME = "application/vnd.google-apps.spreadsheet"


async def create_spreadsheet(provider: Any, args: dict[str, Any]) -> dict[str, Any]:
    parent = args.get("parent_id")
    if parent:
        snapshot = await provider.snapshot("create_spreadsheet", args)
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
            identifier = existing["files"][0]["id"]
            result = provider._result(await provider._metadata(identifier))
            try:
                verified = await matches_created(provider, identifier, args["sheets"])
            except Exception:
                verified = False
            if verified:
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
        current = await provider._metadata(identifier)
        defaults = current.get("sheets", [])
        requests: list[dict[str, Any]] = []
        first_id = defaults[0]["properties"]["sheetId"] if defaults else 0
        next_id = max((item["properties"]["sheetId"] for item in defaults), default=0) + 1
        for index, sheet in enumerate(args["sheets"]):
            sheet_id = first_id if index == 0 else next_id + index - 1
            properties = {
                "sheetId": sheet_id,
                "title": sheet["name"],
                "gridProperties": {
                    "rowCount": max(100, len(sheet["rows"]) + 1),
                    "columnCount": max(26, len(sheet["columns"])),
                },
            }
            if index == 0 and defaults:
                requests.append(
                    {
                        "updateSheetProperties": {
                            "properties": properties,
                            "fields": "title,gridProperties",
                        }
                    }
                )
            else:
                requests.append({"addSheet": {"properties": properties}})
            rows = [sheet["columns"], *sheet["rows"]]
            requests.append(
                update_cells({"sheetId": sheet_id, "startRowIndex": 0, "startColumnIndex": 0}, rows)
            )
            requests.append(
                {
                    "repeatCell": {
                        "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                        "fields": "userEnteredFormat.textFormat.bold",
                    }
                }
            )
        await provider._batch(identifier, requests)
        current = await provider._metadata(identifier)
        if not await matches_created(provider, identifier, args["sheets"]):
            raise ConnectorError(
                "readback_failed", "Created spreadsheet values did not match the approved content"
            )
        return provider._result(current) | {"status": "created", "operation_id": operation}
    except Exception:
        return {
            "id": identifier,
            "title": args["title"],
            "mime_type": MIME,
            "web_url": f"https://docs.google.com/spreadsheets/d/{identifier}/edit",
            "status": "partial",
            "partial": True,
            "verified": False,
            "error_code": "PARTIAL_CREATION",
            "operation_id": operation,
        }
