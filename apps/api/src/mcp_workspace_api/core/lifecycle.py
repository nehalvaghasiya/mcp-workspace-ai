from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from sqlalchemy import update

from mcp_workspace_api.db import (
    Operation,
    Run,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


def application_lifespan(context: ApplicationContext, servers: dict[str, Any]) -> Any:
    db = context.db
    runtime = context.runtime
    app = context.app
    retention_loop = context.retention_service.retention_loop

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        from mcp_workspace_api.db.migrate import migrate

        migrate(db)
        app.state.loop = asyncio.get_running_loop()
        with db.session() as session:
            session.execute(
                update(Run)
                .where(Run.status.in_(["running", "queued"]))
                .values(status="interrupted")
            )
            session.execute(
                update(Operation)
                .where(Operation.status == "dispatched")
                .values(status="outcome_unknown")
            )
        async with AsyncExitStack() as stack:
            for server in servers.values():
                await stack.enter_async_context(server.session_manager.run())
            cleanup_task = asyncio.create_task(retention_loop())
            yield
            cleanup_task.cancel()
            await asyncio.gather(cleanup_task, return_exceptions=True)
            for task in list(runtime.tasks.values()):
                task.cancel()
            await asyncio.gather(*runtime.tasks.values(), return_exceptions=True)
            for adapter in runtime.adapters.values():
                await adapter.aclose()
        db.engine.dispose()

    return lifespan
