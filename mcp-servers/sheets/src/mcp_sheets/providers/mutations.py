from __future__ import annotations

from typing import Any

from mcp_workspace_common.errors import ConnectorError

from mcp_sheets.providers.ranges import cell_data


def update_cells(grid: dict[str, int], rows: list[list[Any]]) -> dict[str, Any]:
    return {
        "updateCells": {
            "start": {
                "sheetId": grid["sheetId"],
                "rowIndex": grid["startRowIndex"],
                "columnIndex": grid["startColumnIndex"],
            },
            "rows": [{"values": [cell_data(cell) for cell in row]} for row in rows],
            "fields": "userEnteredValue",
        }
    }


def format_cells(grid: dict[str, int], args: dict[str, Any]) -> dict[str, Any]:
    formatting: dict[str, Any] = {}
    text = {key: args[key] for key in ("bold", "italic") if args.get(key) is not None}
    if text:
        formatting["textFormat"] = text
    color = args.get("background_color")
    if color:
        formatting["backgroundColor"] = {
            channel: int(color[offset : offset + 2], 16) / 255
            for channel, offset in (("red", 1), ("green", 3), ("blue", 5))
        }
    if args.get("number_format"):
        formatting["numberFormat"] = {"type": args["number_format"]}
    fields = ",".join("userEnteredFormat." + key for key in formatting)
    return {
        "repeatCell": {"range": grid, "cell": {"userEnteredFormat": formatting}, "fields": fields}
    }


def add_chart(grid: dict[str, int], args: dict[str, Any]) -> dict[str, Any]:
    if (
        grid["endColumnIndex"] - grid["startColumnIndex"] < 2
        or grid["endRowIndex"] - grid["startRowIndex"] <= args["header_rows"]
    ):
        raise ConnectorError(
            "invalid_input", "Charts require a domain column and at least one data series"
        )
    domain = grid | {"endColumnIndex": grid["startColumnIndex"] + 1}
    series = [
        {
            "series": {
                "sourceRange": {
                    "sources": [grid | {"startColumnIndex": column, "endColumnIndex": column + 1}]
                }
            },
            "targetAxis": "LEFT_AXIS",
        }
        for column in range(grid["startColumnIndex"] + 1, grid["endColumnIndex"])
    ]
    chart = {
        "spec": {
            "title": args["title"],
            "basicChart": {
                "chartType": args["chart_type"],
                "legendPosition": "BOTTOM_LEGEND",
                "headerCount": args["header_rows"],
                "domains": [{"domain": {"sourceRange": {"sources": [domain]}}}],
                "series": series,
            },
        },
        "position": {
            "overlayPosition": {
                "anchorCell": {
                    "sheetId": grid["sheetId"],
                    "rowIndex": args["anchor_row"],
                    "columnIndex": args["anchor_column"],
                }
            }
        },
    }
    return {"addChart": {"chart": chart}}


def expected_values(rows: list[list[Any]]) -> list[list[Any]]:
    return [[cell.get("value") if isinstance(cell, dict) else cell for cell in row] for row in rows]


def matches_rows(actual: list[list[Any]], expected: list[list[Any]]) -> bool:
    for offset, row in enumerate(expected):
        returned = actual[offset] if offset < len(actual) else []
        for column, value in enumerate(row):
            if (returned[column] if column < len(returned) else None) not in (
                value,
                "" if value is None else value,
            ):
                return False
    return True
