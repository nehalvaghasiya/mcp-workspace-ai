from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from fastapi import HTTPException

from mcp_workspace_api.agents import run_agent

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


class RunService:
    def __init__(self, context: ApplicationContext) -> None:
        self.context = context

    def start_task(self, run_id: str, approval: dict[str, str] | None = None) -> None:
        context = self.context
        runtime = context.runtime
        active = runtime.tasks.get(run_id)
        if active and not active.done():
            raise HTTPException(409, "Run is already active")
        task = asyncio.create_task(run_agent(runtime, run_id, approval))
        runtime.tasks[run_id] = task

        def finished(done: asyncio.Task[None]) -> None:
            if runtime.tasks.get(run_id) is done:
                runtime.tasks.pop(run_id, None)
            if not done.cancelled() and done.exception():
                import logging

                logging.getLogger("workspace.runs").error("Workflow task failed; run_id=%s", run_id)

        task.add_done_callback(finished)
