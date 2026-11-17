from __future__ import annotations

import asyncio
import secrets
from typing import TYPE_CHECKING, Any

from sqlalchemy import update

from mcp_workspace_api.contracts import (
    ToolDefinition,
    digest,
)
from mcp_workspace_api.core.security import Denied, secret_hash
from mcp_workspace_api.db import (
    Approval,
    Artifact,
    Operation,
    Run,
    now,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.execution_context import Runtime


class ApprovalService:
    def __init__(self, context: Runtime) -> None:
        self.context = context

    async def propose(
        self, user_id: str, run_id: str, name: str, arguments: dict[str, Any]
    ) -> Approval:
        context = self.context
        definition = context.tools[name]
        account_id = context.policy.authorize(user_id, definition)
        clean = context.validate_arguments(user_id, definition, arguments).model_dump(mode="json")
        snapshot = await context.adapter(user_id).snapshot(
            definition.server, name.split(".")[1], clean
        )
        if name == "drive.upload_artifact":
            with context.db.session() as session:
                artifact = session.get(Artifact, clean["artifact_id"])
                if not artifact or artifact.user_id != user_id:
                    raise Denied("PERMISSION_DENIED", "Artifact is unavailable")
                snapshot["artifact_sha256"] = artifact.sha256
        if name in {"gmail.create_draft", "gmail.update_draft"} and clean.get("attachment_ids"):
            snapshot["attachment_sha256s"] = self.attachments(
                user_id, clean["attachment_ids"], hashes=True
            )
        action = digest(
            {
                "user": user_id,
                "account": account_id,
                "tool": name,
                "args": clean,
                "snapshot": snapshot,
            }
        )
        with context.db.session() as session:
            approval = Approval(
                user_id=user_id,
                run_id=run_id,
                tool=name,
                arguments=clean,
                snapshot=snapshot,
                account_id=account_id,
                action_digest=action,
                expires_at=now() + context.settings.approval_ttl,
            )
            session.add(approval)
            session.flush()
            return approval

    async def _write(
        self,
        claims: dict[str, Any],
        definition: ToolDefinition,
        args: dict[str, Any],
        account_id: str,
    ) -> dict[str, Any]:
        context = self.context
        authorization = claims.get("approval") or {}
        with context.db.session() as session:
            approval = session.get(Approval, authorization.get("id", ""))
            if (
                not approval
                or approval.user_id != claims["user_id"]
                or approval.account_id != account_id
                or approval.tool != definition.name
                or approval.run_id != claims.get("run_id")
            ):
                raise Denied("APPROVAL_REQUIRED", "Exact-action approval is required")
            if approval.expires_at < now():
                raise Denied("APPROVAL_EXPIRED", "Review this action again")
            if approval.status != "approved" or not secrets.compare_digest(
                approval.capability_hash, secret_hash(authorization.get("secret", ""))
            ):
                raise Denied("PERMISSION_DENIED", "Approval is invalid or already used")
            snapshot = approval.snapshot
            expected = digest(
                {
                    "user": claims["user_id"],
                    "account": account_id,
                    "tool": definition.name,
                    "args": args,
                    "snapshot": snapshot,
                }
            )
            if not secrets.compare_digest(expected, approval.action_digest):
                raise Denied("PERMISSION_DENIED", "Approved arguments changed")
        current = await context.adapter(claims["user_id"]).snapshot(
            definition.server, definition.name.split(".")[1], args
        )
        comparable = {
            k: v for k, v in snapshot.items() if k not in {"artifact_sha256", "attachment_sha256s"}
        }
        if digest(current) != digest(comparable):
            raise Denied(
                "PERMISSION_DENIED", "The target changed after approval; review a fresh proposal"
            )
        preflight: dict[str, Any] = {}
        if definition.name in {"gmail.create_draft", "gmail.update_draft"} and args.get(
            "attachment_ids"
        ):
            attachments = self.attachments(claims["user_id"], args["attachment_ids"])
            if {item["id"]: item["sha256"] for item in attachments} != snapshot.get(
                "attachment_sha256s"
            ):
                raise Denied("PERMISSION_DENIED", "An approved attachment changed")
            preflight["_attachments"] = attachments
        if definition.name == "drive.upload_artifact":
            with context.db.session() as session:
                artifact = session.get(Artifact, args["artifact_id"])
                if (
                    not artifact
                    or artifact.user_id != claims["user_id"]
                    or artifact.sha256 != snapshot["artifact_sha256"]
                ):
                    raise Denied("PERMISSION_DENIED", "Artifact changed")
                preflight["_artifact"] = {
                    "path": str(context.settings.storage / artifact.storage_key),
                    "title": artifact.title,
                    "mime_type": artifact.mime_type,
                    "sha256": artifact.sha256,
                }
        if approval.expires_at < now():
            raise Denied("APPROVAL_EXPIRED", "Review this action again")
        with context.db.session() as session:
            claimed = session.execute(
                update(Approval)
                .where(
                    Approval.id == approval.id,
                    Approval.status == "approved",
                    Approval.expires_at >= now(),
                )
                .values(status="consumed")
                .returning(Approval.id)
            )
            if claimed.scalar_one_or_none() is None:
                raise Denied("PERMISSION_DENIED", "Approval was already consumed")
            run = session.get(Run, approval.run_id)
            if not run or run.status in {"cancelled", "failed", "interrupted"}:
                raise Denied("PERMISSION_DENIED", "Run is no longer executable")
            operation = Operation(user_id=claims["user_id"], approval_id=approval.id)
            session.add(operation)
            session.flush()
            operation_id = operation.id
        internal = {**args, **preflight, "_snapshot": comparable, "idempotency_key": operation_id}
        try:
            data = await asyncio.wait_for(
                context.adapter(claims["user_id"]).call(
                    definition.server, definition.name.split(".")[1], internal
                ),
                context.settings.tool_timeout,
            )
        except BaseException:
            with context.db.session() as session:
                row = session.get(Operation, operation_id)
                if row:
                    row.status = "outcome_unknown"
            raise Denied(
                "OUTCOME_UNKNOWN",
                "Write outcome is unknown. Inspect the provider before creating another action.",
            ) from None
        with context.db.session() as session:
            row = session.get(Operation, operation_id)
            if row:
                row.status, row.result = "partial" if data.get("partial") else "completed", data
        return {**data, "operation_id": operation_id}

    def attachments(self, user_id: str, ids: list[str], *, hashes: bool = False) -> Any:
        attachments = []
        with self.context.db.session() as session:
            for artifact_id in ids:
                artifact = session.get(Artifact, artifact_id)
                if not artifact or artifact.user_id != user_id or not artifact.validated:
                    raise Denied(
                        "PERMISSION_DENIED",
                        "An attachment is unavailable or is not owned by this account",
                    )
                attachments.append(
                    {
                        "id": artifact.id,
                        "path": str(self.context.settings.storage / artifact.storage_key),
                        "title": artifact.title,
                        "mime_type": artifact.mime_type,
                        "sha256": artifact.sha256,
                    }
                )
        return {item["id"]: item["sha256"] for item in attachments} if hashes else attachments
