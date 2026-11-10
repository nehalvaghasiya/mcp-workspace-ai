from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Any

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select, update

from mcp_workspace_api.core.execution_context import (
    approval_json,
)
from mcp_workspace_api.core.security import secret_hash
from mcp_workspace_api.db import (
    Approval,
    Run,
    User,
    now,
)
from mcp_workspace_api.db.repositories.ownership import owned
from mcp_workspace_api.schemas.requests.decision import Decision
from mcp_workspace_api.schemas.responses import (
    ApprovalView,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.application_context import ApplicationContext


def register(app: FastAPI, context: ApplicationContext) -> None:
    db = context.db
    runtime = context.runtime
    app = context.app
    require_user = context.session_service.require_user
    start_task = context.run_service.start_task

    @app.get("/api/approvals", response_model=list[ApprovalView])
    async def approvals(user: User = Depends(require_user)) -> list[dict[str, Any]]:
        expired_runs = []
        with db.session() as session:
            for row in session.scalars(
                select(Approval).where(
                    Approval.user_id == user.id,
                    Approval.status == "pending",
                    Approval.expires_at < now(),
                )
            ):
                run = session.get(Run, row.run_id)
                if run and run.status == "needs_approval":
                    run.status, run.error = "failed", "Approval expired; request a fresh proposal"
                    expired_runs.append(run.id)
            session.execute(
                update(Approval)
                .where(
                    Approval.user_id == user.id,
                    Approval.status == "pending",
                    Approval.expires_at < now(),
                )
                .values(status="expired")
            )
            result = [
                approval_json(row)
                for row in session.scalars(
                    select(Approval)
                    .where(Approval.user_id == user.id)
                    .order_by(Approval.created_at.desc())
                    .limit(100)
                )
            ]
        for run_id in expired_runs:
            runtime.emit(
                run_id,
                "run.failed",
                {
                    "code": "APPROVAL_EXPIRED",
                    "message": "Approval expired; request a fresh proposal",
                },
            )
        return result

    @app.post("/api/approvals/{approval_id}/decide")
    async def decide(
        approval_id: str, body: Decision, user: User = Depends(require_user)
    ) -> dict[str, str]:
        capability = secrets.token_urlsafe(32)
        with db.session() as session:
            row = owned(session, Approval, approval_id, user)
            if row.status != "pending" or row.expires_at < now():
                raise HTTPException(409, "Approval is stale, expired, or already decided")
            run = owned(session, Run, row.run_id, user)
            if run.status != "needs_approval":
                raise HTTPException(409, "Run is no longer waiting for this approval")
            status = "approved" if body.decision == "approve" else "rejected"
            claimed = session.execute(
                update(Approval)
                .where(Approval.id == row.id, Approval.status == "pending")
                .values(status=status, capability_hash=secret_hash(capability))
                .returning(Approval.id)
            )
            if claimed.scalar_one_or_none() is None:
                raise HTTPException(409, "Approval was already decided")
            if body.decision == "reject":
                run.status, run.error = "cancelled", "Action rejected by user"
        if body.decision == "approve":
            start_task(row.run_id, {"id": row.id, "secret": capability})
        else:
            runtime.emit(row.run_id, "run.cancelled", {"reason": "Action rejected"})
        return {"status": status}
