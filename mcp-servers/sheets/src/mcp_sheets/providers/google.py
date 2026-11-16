from __future__ import annotations

from typing import Any
from urllib.parse import quote

from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.providers.google_client import GoogleClient
from mcp_workspace_common.providers.identifiers import _identifier
from pydantic import BaseModel

from mcp_sheets.providers.create import create_spreadsheet
from mcp_sheets.providers.mutations import (
    add_chart,
    expected_values,
    format_cells,
    matches_rows,
    update_cells,
)
from mcp_sheets.providers.ranges import grid_range
from mcp_sheets.providers.verification import matches_formatting
from mcp_sheets.schemas.add_chart import AddChart
from mcp_sheets.schemas.add_sheet import AddSheet
from mcp_sheets.schemas.create_spreadsheet import CreateSpreadsheet
from mcp_sheets.schemas.format_range import FormatRange
from mcp_sheets.schemas.range_request import RangeRequest
from mcp_sheets.schemas.spreadsheet_id import SpreadsheetId
from mcp_sheets.schemas.write_range import WriteRange

BASE = "https://sheets.googleapis.com/v4/spreadsheets/"
DRIVE = "https://www.googleapis.com/drive/v3/files"


class GoogleSheets:
    def __init__(self, transport: GoogleClient) -> None:
        self._request = transport.request

    async def _metadata(self, identifier: str) -> dict[str, Any]:
        return dict(
            await self._request(
                "GET",
                BASE + _identifier(identifier),
                read=True,
                params={
                    "fields": "spreadsheetId,spreadsheetUrl,properties,sheets(properties,charts)"
                },
            )
        )

    async def _read(
        self, identifier: str, selected: str, rendering: str = "FORMULA"
    ) -> dict[str, Any]:
        return dict(
            await self._request(
                "GET",
                BASE + _identifier(identifier) + "/values/" + quote(selected, safe=""),
                read=True,
                params={"valueRenderOption": rendering, "dateTimeRenderOption": "SERIAL_NUMBER"},
            )
        )

    async def _batch(self, identifier: str, requests: list[dict[str, Any]]) -> dict[str, Any]:
        return dict(
            await self._request(
                "POST",
                BASE + _identifier(identifier) + ":batchUpdate",
                json={"requests": requests, "includeSpreadsheetInResponse": False},
            )
        )

    def _result(self, metadata: dict[str, Any]) -> dict[str, Any]:
        identifier = metadata.get("spreadsheetId", metadata.get("id", ""))
        title = metadata.get("properties", {}).get("title", metadata.get("name", identifier))
        url = f"https://docs.google.com/spreadsheets/d/{identifier}/edit"
        return {
            "id": identifier,
            "title": title,
            "mime_type": "application/vnd.google-apps.spreadsheet",
            "web_url": url,
            "spreadsheet": metadata,
            "sources": [
                {"provider": "sheets", "resource_id": identifier, "title": title, "url": url}
            ],
            "verified": True,
        }

    async def snapshot(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if tool == "create_spreadsheet":
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
        if tool in {"get_spreadsheet", "read_range"}:
            return {}
        identifier = args["spreadsheet_id"]
        metadata = await self._metadata(identifier)
        snapshot = {
            "spreadsheet_id": identifier,
            "title": metadata.get("properties", {}).get("title", ""),
            "metadata": metadata,
        }
        if args.get("range"):
            snapshot["grid"] = grid_range(args["range"], metadata)
            snapshot["range"] = args["range"]
            snapshot["values"] = (await self._read(identifier, args["range"])).get("values", [])
        if tool == "format_range":
            snapshot["formatting"] = await self._request(
                "GET",
                BASE + identifier,
                read=True,
                params={
                    "ranges": args["range"],
                    "includeGridData": "true",
                    "fields": "sheets(data(startRow,startColumn,rowData(values(userEnteredFormat))))",
                },
            )
        return snapshot

    async def call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        models: dict[str, type[BaseModel]] = {
            "get_spreadsheet": SpreadsheetId,
            "read_range": RangeRequest,
            "create_spreadsheet": CreateSpreadsheet,
            "write_range": WriteRange,
            "append_rows": WriteRange,
            "format_range": FormatRange,
            "add_chart": AddChart,
            "add_sheet": AddSheet,
        }
        if tool not in models:
            raise ConnectorError("unknown_tool", "Unknown Google Sheets tool")
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
        if tool == "create_spreadsheet":
            return await create_spreadsheet(self, args)
        identifier = args["spreadsheet_id"]
        if tool == "get_spreadsheet":
            return self._result(await self._metadata(identifier))
        if tool == "read_range":
            metadata = await self._metadata(identifier)
            grid_range(args["range"], metadata)
            formula_data = await self._read(identifier, args["range"])
            return (
                self._result(metadata)
                | await self._read(identifier, args["range"], "UNFORMATTED_VALUE")
                | {"formula_values": formula_data.get("values", [])}
            )
        approved = args.get("_snapshot")
        current = await self.snapshot(tool, args)
        if not approved or current != approved:
            raise ConnectorError(
                "stale_action", "Spreadsheet changed or approved snapshot is missing"
            )
        grid = dict(current.get("grid", {}))
        if tool in {"write_range", "append_rows"}:
            if tool == "append_rows":
                existing = current["values"]
                used = max(
                    (
                        index + 1
                        for index, row in enumerate(existing)
                        if any(cell not in (None, "") for cell in row)
                    ),
                    default=0,
                )
                grid["startRowIndex"] += used
                if grid["startRowIndex"] + len(args["values"]) > grid["endRowIndex"]:
                    raise ConnectorError("invalid_input", "Appended rows exceed the approved range")
            reply = await self._batch(identifier, [update_cells(grid, args["values"])])
            read = await self._read(identifier, args["range"])
            offset = grid["startRowIndex"] - current["grid"]["startRowIndex"]
            if not matches_rows(read.get("values", [])[offset:], expected_values(args["values"])):
                raise ConnectorError(
                    "readback_failed",
                    "Written spreadsheet values could not be verified; inspect before retrying",
                )
        elif tool == "format_range":
            reply = await self._batch(identifier, [format_cells(grid, args)])
        elif tool == "add_chart":
            reply = await self._batch(identifier, [add_chart(grid, args)])
        else:
            if any(
                sheet["properties"]["title"].casefold() == args["title"].casefold()
                for sheet in current["metadata"].get("sheets", [])
            ):
                raise ConnectorError("invalid_input", "A worksheet with that title already exists")
            reply = await self._batch(
                identifier,
                [
                    {
                        "addSheet": {
                            "properties": {
                                "title": args["title"],
                                "gridProperties": {
                                    "rowCount": args["row_count"],
                                    "columnCount": args["column_count"],
                                },
                            }
                        }
                    }
                ],
            )
        refreshed = await self._metadata(identifier)
        if tool == "format_range":
            actual_formatting = await self._request(
                "GET",
                BASE + identifier,
                read=True,
                params={
                    "ranges": args["range"],
                    "includeGridData": "true",
                    "fields": "sheets(data(startRow,startColumn,rowData(values(userEnteredFormat))))",
                },
            )
            expected_formatting = format_cells(grid, args)["repeatCell"]["cell"][
                "userEnteredFormat"
            ]
            if not matches_formatting(actual_formatting, grid, expected_formatting):
                raise ConnectorError(
                    "readback_failed",
                    "Spreadsheet formatting could not be verified; inspect before retrying",
                )
        if tool == "add_chart":
            chart_ids = [
                item["addChart"]["chart"]["chartId"]
                for item in reply.get("replies", [])
                if item.get("addChart", {}).get("chart", {}).get("chartId") is not None
            ]
            current_ids = {
                chart["chartId"]
                for sheet in refreshed.get("sheets", [])
                for chart in sheet.get("charts", [])
            }
            if not chart_ids or not set(chart_ids) <= current_ids:
                raise ConnectorError(
                    "readback_failed",
                    "Created chart could not be verified; inspect before retrying",
                )
        if tool == "add_sheet" and not any(
            sheet["properties"]["title"] == args["title"] for sheet in refreshed.get("sheets", [])
        ):
            raise ConnectorError(
                "readback_failed",
                "Created worksheet could not be verified; inspect before retrying",
            )
        result = self._result(refreshed) | {
            "status": "updated",
            "operation_id": args.get("idempotency_key"),
            "update": reply,
        }
        if args.get("range"):
            result |= {
                "range": args["range"],
                "values": (await self._read(identifier, args["range"])).get("values", []),
            }
        return result
