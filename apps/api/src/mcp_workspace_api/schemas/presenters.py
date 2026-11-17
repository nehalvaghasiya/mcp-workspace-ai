from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp_workspace_api.services.run_recovery import recovery_details

if TYPE_CHECKING:
    from mcp_workspace_api.core.execution_context import Runtime

from mcp_workspace_api.db import (
    Run,
)


def run_json(run: Run, runtime: Runtime | None = None) -> dict[str, Any]:
    return {
        "id": run.id,
        "conversation_id": run.conversation_id,
        "status": run.status,
        "error": run.error or None,
        **(recovery_details(runtime, run) if runtime else {}),
    }
