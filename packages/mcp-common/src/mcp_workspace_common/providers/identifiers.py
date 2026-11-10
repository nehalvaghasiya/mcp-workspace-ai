from __future__ import annotations

from typing import Any
from urllib.parse import quote

from mcp_workspace_common.errors import ConnectorError


def _identifier(value: Any) -> str:
    value = str(value)
    if (
        not value
        or len(value) > 300
        or any(c in value for c in "\r\n\\/?#")
        or value in {".", ".."}
    ):
        raise ConnectorError("invalid_input", "Invalid provider resource identifier")
    return quote(value, safe="")
