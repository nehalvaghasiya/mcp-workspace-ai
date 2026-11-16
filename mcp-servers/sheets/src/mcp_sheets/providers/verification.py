from __future__ import annotations

from typing import Any

from mcp_sheets.providers.mutations import expected_values, matches_rows


async def matches_created(provider: Any, identifier: str, sheets: list[dict[str, Any]]) -> bool:
    for sheet in sheets:
        column = ""
        number = len(sheet["columns"])
        while number:
            number, remainder = divmod(number - 1, 26)
            column = chr(65 + remainder) + column
        name = sheet["name"].replace("'", "''")
        selected = f"'{name}'!A1:{column}{len(sheet['rows']) + 1}"
        read = await provider._read(identifier, selected)
        if not matches_rows(
            read.get("values", []), expected_values([sheet["columns"], *sheet["rows"]])
        ):
            return False
    return True


def contains_format(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            actual = {}
        return all(contains_format(actual.get(key), value) for key, value in expected.items())
    if isinstance(expected, bool):
        return (False if actual is None else actual) == expected
    if isinstance(expected, (int, float)):
        return abs((0 if actual is None else actual) - expected) < 0.0001
    return actual == expected


def matches_formatting(
    payload: dict[str, Any], grid: dict[str, int], expected: dict[str, Any]
) -> bool:
    actual: dict[tuple[int, int], dict[str, Any]] = {}
    for sheet in payload.get("sheets", []):
        for data in sheet.get("data", []):
            for row_index, row in enumerate(data.get("rowData", []), data.get("startRow", 0)):
                for column, value in enumerate(row.get("values", []), data.get("startColumn", 0)):
                    actual[(row_index, column)] = value.get("userEnteredFormat", {})
    return all(
        contains_format(actual.get((row, column), {}), expected)
        for row in range(grid["startRowIndex"], grid["endRowIndex"])
        for column in range(grid["startColumnIndex"], grid["endColumnIndex"])
    )
