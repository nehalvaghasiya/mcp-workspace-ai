from __future__ import annotations

import re
import shlex
from typing import Any

from mcp_workspace_common.errors import ConnectorError


def _drive_match(item: dict[str, Any], query: str) -> bool:
    if not query:
        return True
    if not re.match(r"^(?:name|fullText|mimeType|trashed)\s|^'", query):
        return query.lower() in (item["name"] + " " + item.get("content", "")).lower()
    # A deliberately limited grammar: AND expressions with quoted strings. Live
    # Google queries pass through to the provider; unsupported mock syntax fails.
    try:
        tokens = shlex.split(query)
    except ValueError:
        raise ConnectorError("invalid_query", "Invalid Drive query quoting") from None
    index = 0
    while index < len(tokens):
        if index + 2 >= len(tokens):
            raise ConnectorError("unsupported_query", "Unsupported mock Drive query")
        field, operator, value = tokens[index : index + 3]
        if operator == "contains" and field in {"name", "fullText"}:
            target = item["name"] + (" " + item.get("content", "") if field == "fullText" else "")
            matched = value.lower() in target.lower()
        elif operator == "=" and field == "mimeType":
            matched = value == item["mimeType"]
        elif operator == "=" and field == "trashed" and value in {"true", "false"}:
            matched = bool(item.get("trashed")) == (value == "true")
        elif operator == "in" and value == "parents":
            matched = field in item.get("parents", [])
        else:
            raise ConnectorError(
                "unsupported_query",
                "Mock Drive query supports name/fullText contains, MIME, parents, trashed and AND",
            )
        if not matched:
            return False
        index += 3
        if index < len(tokens):
            if tokens[index].lower() != "and":
                raise ConnectorError(
                    "unsupported_query", "Mock Drive query supports AND expressions only"
                )
            index += 1
    return True
