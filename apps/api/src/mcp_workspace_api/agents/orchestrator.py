from __future__ import annotations

import asyncio

from mcp_workspace_api.agents.executor import execute_run
from mcp_workspace_api.core.execution_context import Runtime
from mcp_workspace_api.core.security import Denied
from mcp_workspace_api.db import Run


async def run_agent(runtime: Runtime, run_id: str, approved: dict[str, str] | None = None) -> None:
    try:
        async with asyncio.timeout(runtime.settings.run_timeout):
            await execute_run(runtime, run_id, approved)
    except asyncio.CancelledError:
        with runtime.db.session() as session:
            run = session.get(Run, run_id)
            if run and run.status not in {"completed", "failed"}:
                run.status = "cancelled"
        runtime.emit(run_id, "run.cancelled", {})
    except Exception as exc:
        code = getattr(exc, "code", "RUN_FAILED")
        message = (
            str(exc)
            if isinstance(exc, Denied)
            else "The workflow could not complete. Inspect its trace and retry safe read operations."
        )
        with runtime.db.session() as session:
            run = session.get(Run, run_id)
            if run:
                run.status, run.error = "failed", message
        runtime.emit(run_id, "run.failed", {"code": code, "message": message})
