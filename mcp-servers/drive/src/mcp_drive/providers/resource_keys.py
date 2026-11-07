from __future__ import annotations

import re
from typing import Any

from mcp_workspace_common.errors import ConnectorError


def _resource_headers(args: dict[str, Any]) -> dict[str, str]:
    key = args.get("resource_key")
    if key is None:
        return {}
    file_id = args.get("file_id")
    if (
        not isinstance(key, str)
        or not isinstance(file_id, str)
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,300}", key)
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,300}", file_id)
    ):
        raise ConnectorError("invalid_input", "Invalid Drive resource key or file identifier")
    return {"X-Goog-Drive-Resource-Keys": f"{file_id}/{key}"}
