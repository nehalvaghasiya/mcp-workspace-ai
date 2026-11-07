from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.extraction import MAX_FILE_BYTES


def _artifact_bytes(artifact: dict[str, Any]) -> bytes:
    # Paths are injected after the host's artifact owner/sandbox check. They are
    # deliberately absent from the public MCP schema.
    try:
        path = Path(artifact["path"])
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ConnectorError("file_too_large", "Upload exceeds 10 MiB limit")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != artifact["sha256"]:
            raise ConnectorError("stale_action", "Artifact changed after approval")
        return data
    except (OSError, KeyError):
        raise ConnectorError("artifact_unavailable", "Verified artifact is unavailable") from None
