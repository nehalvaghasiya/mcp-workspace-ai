from __future__ import annotations

import re
from typing import Any

from mcp_workspace_common.errors import ConnectorError

PATTERN = re.compile(
    r"^(?:(?P<sheet>'(?:[^'\r\n]|'')+'|[A-Za-z0-9_ ]+)!)?(?P<left>[A-Z]{1,3})(?P<top>[1-9][0-9]{0,5})(?::(?P<right>[A-Z]{1,3})(?P<bottom>[1-9][0-9]{0,5}))?$"
)


def column_number(value: str) -> int:
    number = 0
    for char in value:
        number = number * 26 + ord(char) - 64
    return number


def parse_range(value: str) -> tuple[str | None, int, int, int, int]:
    match = PATTERN.fullmatch(value)
    if not match:
        raise ValueError("Use a bounded A1 cell range, for example 'Budget'!A1:F100")
    left, right = column_number(match["left"]), column_number(match["right"] or match["left"])
    top, bottom = int(match["top"]), int(match["bottom"] or match["top"])
    if (
        bottom < top
        or right < left
        or right > 16384
        or bottom > 1000000
        or (bottom - top + 1) * (right - left + 1) > 20000
    ):
        raise ValueError("Range must contain at most 20000 cells with increasing bounds")
    sheet = match["sheet"]
    if sheet and sheet.startswith("'"):
        sheet = sheet[1:-1].replace("''", "'")
    return sheet, top - 1, bottom, left - 1, right


def grid_range(value: str, metadata: dict[str, Any]) -> dict[str, int]:
    title, top, bottom, left, right = parse_range(value)
    sheets = metadata.get("sheets", [])
    properties = next(
        (
            sheet["properties"]
            for sheet in sheets
            if title is None or sheet["properties"].get("title") == title
        ),
        None,
    )
    if not properties:
        raise ConnectorError("not_found", "The selected spreadsheet tab is unavailable")
    return {
        "sheetId": properties["sheetId"],
        "startRowIndex": top,
        "endRowIndex": bottom,
        "startColumnIndex": left,
        "endColumnIndex": right,
    }


def cell_data(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        kind, value = value["type"], value["value"]
        field = {
            "string": "stringValue",
            "number": "numberValue",
            "date": "stringValue",
            "formula": "formulaValue",
        }[kind]
    elif isinstance(value, bool):
        field = "boolValue"
    elif isinstance(value, (int, float)):
        field = "numberValue"
    else:
        field = "stringValue"
    return {"userEnteredValue": {field: value}}
