from __future__ import annotations

from typing import Any

from mcp_workspace_common.errors import ConnectorError


def _find(items: list[dict[str, Any]], rid: str) -> dict[str, Any]:
    for item in items:
        if item.get("id") == rid:
            return item
    raise ConnectorError("not_found", "Resource not found or inaccessible")
