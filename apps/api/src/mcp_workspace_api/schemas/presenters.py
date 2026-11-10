from __future__ import annotations

from typing import Any

from mcp_workspace_api.db import (
    Run,
)


def run_json(run: Run) -> dict[str, Any]:
    return {
        "id": run.id,
        "conversation_id": run.conversation_id,
        "status": run.status,
        "error": run.error or None,
    }
