"""Carry bounded read evidence across follow-ups without replaying effects."""

from __future__ import annotations

import json
from typing import Any

from mcp_workspace_api.contracts import Risk, ToolDefinition


def merge_read_evidence(
    definitions: dict[str, ToolDefinition],
    previous: list[dict[str, Any]],
    current: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for result in [*previous, *current]:
        definition = definitions.get(result.get("tool", ""))
        if not definition or definition.risk != Risk.READ:
            continue
        data = result.get("data", {})
        identifiers = sorted(
            (row["provider"], row["resource_id"]) for row in result.get("sources", [])
        )
        if not identifiers:
            identifiers = [
                (
                    "record",
                    str(data.get("id") or data.get("file_id") or data.get("thread_id") or ""),
                )
            ]
            for key in ("messages", "events", "files"):
                identifiers.extend(
                    (key, str(row.get("id", "")))
                    for row in data.get(key, [])
                    if isinstance(row, dict)
                )
        key = json.dumps([result["tool"], identifiers])
        records.pop(key, None)
        records[key] = result
    return list(records.values())[-24:]
