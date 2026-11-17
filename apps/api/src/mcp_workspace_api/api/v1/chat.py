from __future__ import annotations

import asyncio
import copy
import json
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, update

from mcp_workspace_api.core.execution_context import (
    timestamp,
)
from mcp_workspace_api.db import (
    Approval,
    Conversation,
    Message,
    Run,
    RunEvent,
    User,
)
from mcp_workspace_api.db.repositories.ownership import owned
from mcp_workspace_api.schemas.presenters import run_json
from mcp_workspace_api.schemas.requests.new_message import NewMessage
from mcp_workspace_api.schemas.requests.retry_run import RetryRun
from mcp_workspace_api.schemas.responses import (
    RunView,
    StreamEvent,
)
from mcp_workspace_api.services.run_recovery import recovery_details

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


def register(app: FastAPI, context: ApplicationContext) -> None:
    db = context.db
    runtime = context.runtime
    app = context.app
    require_user = context.session_service.require_user
    start_task = context.run_service.start_task

    @app.post("/api/conversations/{conversation_id}/messages", response_model=RunView)
    async def send_message(
        conversation_id: str, body: NewMessage, user: User = Depends(require_user)
    ) -> dict[str, Any]:
        with db.session() as session:
            conv = owned(session, Conversation, conversation_id, user)
            request_id = user.id + ":" + body.request_id
            existing = session.scalar(select(Run).where(Run.request_id == request_id))
            if existing:
                if existing.conversation_id != conversation_id or existing.prompt != body.content:
                    raise HTTPException(409, "Request ID was already used for different content")
                return run_json(existing)
            active = list(
                session.scalars(
                    select(Run).where(
                        Run.user_id == user.id,
                        Run.status.in_(["running", "queued", "needs_approval"]),
                    )
                )
            )
            if len(active) >= 2:
                raise HTTPException(
                    429, "Finish or cancel existing workflows before starting another"
                )
            run = Run(
                user_id=user.id, conversation_id=conv.id, request_id=request_id, prompt=body.content
            )
            session.add(run)
            session.add(
                Message(user_id=user.id, conversation_id=conv.id, role="user", content=body.content)
            )
            if conv.title == "New conversation":
                conv.title = (
                    body.content
                    if len(body.content) <= 80
                    else body.content[:77].rsplit(" ", 1)[0] + "…"
                )
            session.flush()
            result = run_json(run)
        start_task(run.id)
        return result

    @app.post("/api/runs/{run_id}/retry", response_model=RunView)
    async def retry_run(
        run_id: str, body: RetryRun, user: User = Depends(require_user)
    ) -> dict[str, Any]:
        with db.session() as session:
            source = owned(session, Run, run_id, user)
            request_id = user.id + ":retry:" + body.request_id
            existing = session.scalar(select(Run).where(Run.request_id == request_id))
            if existing:
                if existing.state.get("retry_of") != source.id:
                    raise HTTPException(409, "Request ID was already used for another retry")
                return run_json(existing, runtime)
            latest = session.scalar(
                select(Run)
                .where(Run.conversation_id == source.conversation_id, Run.user_id == user.id)
                .order_by(Run.created_at.desc())
                .limit(1)
            )
            if (
                not latest
                or latest.id != source.id
                or not recovery_details(runtime, source)["retryable"]
            ):
                raise HTTPException(
                    409, "This run cannot be continued. Review activity and start a new request."
                )
            active_count = list(
                session.scalars(
                    select(Run).where(
                        Run.user_id == user.id,
                        Run.status.in_(["running", "queued", "needs_approval"]),
                    )
                )
            )
            if len(active_count) >= 2:
                raise HTTPException(429, "Finish or cancel existing workflows before continuing")
            if runtime.settings.llm_provider == "openai_compatible" and (
                not user.llm_consent
                or user.consent_provider
                != runtime.settings.llm_base_url + ":" + runtime.settings.llm_model
            ):
                raise HTTPException(403, "Review model processing consent in Settings first")
            for result in source.state.get("results", []):
                runtime.policy.authorize(user.id, runtime.tools[result["tool"]])
            state = copy.deepcopy(source.state)
            for key in ("error_code", "retry_child", "pending_step"):
                state.pop(key, None)
            state["retry_of"] = source.id
            child = Run(
                user_id=user.id,
                conversation_id=source.conversation_id,
                prompt=source.prompt,
                request_id=request_id,
                state=state,
            )
            session.add(child)
            session.flush()
            claimed = session.execute(
                update(Run)
                .where(Run.id == source.id, Run.state == source.state)
                .values(state={**source.state, "retry_child": child.id})
                .returning(Run.id)
            )
            if claimed.scalar_one_or_none() is None:
                raise HTTPException(409, "A continuation already exists; refresh this conversation")
            result = run_json(child, runtime)
        start_task(child.id)
        return result

    @app.get("/api/runs/{run_id}/events")
    async def events(
        run_id: str, request: Request, user: User = Depends(require_user)
    ) -> StreamingResponse:
        with db.session() as session:
            owned(session, Run, run_id, user)
        try:
            after = max(0, int(request.headers.get("Last-Event-ID", "0")))
        except ValueError:
            raise HTTPException(400, "Invalid event cursor") from None

        async def stream() -> AsyncIterator[str]:
            cursor = after
            while True:
                with db.session() as session:
                    current = session.get(Run, run_id)
                    if not current:
                        return
                    rows = list(
                        session.scalars(
                            select(RunEvent)
                            .where(
                                RunEvent.run_id == run_id,
                                RunEvent.user_id == user.id,
                                RunEvent.sequence > cursor,
                            )
                            .order_by(RunEvent.sequence)
                        )
                    )
                    terminal = current.status in {"completed", "failed", "cancelled", "interrupted"}
                for event in rows:
                    cursor = event.sequence
                    payload = StreamEvent.model_validate(
                        {
                            "id": event.sequence,
                            "run_id": run_id,
                            "type": event.type,
                            "data": event.data,
                        }
                    ).model_dump(mode="json")
                    yield f"id: {cursor}\ndata: {json.dumps(payload)}\n\n"
                if terminal:
                    return
                if await request.is_disconnected():
                    return
                yield ": heartbeat\n\n"
                await asyncio.sleep(0.25)

        return StreamingResponse(
            stream(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"}
        )

    @app.get("/api/runs/{run_id}/trace")
    async def trace(run_id: str, user: User = Depends(require_user)) -> list[dict[str, Any]]:
        with db.session() as session:
            owned(session, Run, run_id, user)
            return [
                {
                    "id": row.id,
                    "type": row.type,
                    "created_at": timestamp(row.created_at),
                    **row.data,
                }
                for row in session.scalars(
                    select(RunEvent)
                    .where(
                        RunEvent.run_id == run_id,
                        RunEvent.user_id == user.id,
                        RunEvent.type.in_(["tool.started", "tool.completed"]),
                    )
                    .order_by(RunEvent.sequence)
                )
            ]

    @app.post("/api/runs/{run_id}/cancel")
    async def cancel(run_id: str, user: User = Depends(require_user)) -> dict[str, str]:
        with db.session() as session:
            row = owned(session, Run, run_id, user)
            if row.status in {"completed", "failed"}:
                return {"status": row.status}
            row.status = "cancelled"
            session.execute(
                update(Approval)
                .where(Approval.run_id == run_id, Approval.status.in_(["pending", "approved"]))
                .values(status="revoked")
            )
        task = runtime.tasks.get(run_id)
        if task:
            task.cancel()
        runtime.emit(run_id, "run.cancelled", {})
        return {"status": "cancelled"}
