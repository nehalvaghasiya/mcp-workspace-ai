from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import TYPE_CHECKING

from mcp_workspace_common.execution.context import caller
from pydantic import BaseModel, ValidationError

from mcp_workspace_api.contracts import (
    ToolResult,
)
from mcp_workspace_api.core.security import Denied
from mcp_workspace_api.db import (
    uid,
)

if TYPE_CHECKING:
    from mcp_workspace_api.core.execution_context import Runtime


class Gateway:
    def __init__(self, context: Runtime) -> None:
        self.context = context

    async def execute(self, name: str, request: BaseModel) -> ToolResult:
        context = self.context
        """Called by the MCP handler after transport authentication, never by the agent."""
        claims = caller.get()
        user_id, run_id = claims["user_id"], claims.get("run_id", "")
        definition = context.tools[name]
        account_id = context.policy.authorize(user_id, definition)
        args = request.model_dump(mode="json")
        if (
            "timezone" in definition.input_model.model_fields
            and "timezone" not in request.model_fields_set
        ):
            args = context.validate_arguments(
                user_id, definition, request.model_dump(mode="json", exclude_unset=True)
            ).model_dump(mode="json")
        started = time.perf_counter()
        try:
            if context.policy.needs_approval(definition):
                async with context.write_locks.setdefault(user_id, asyncio.Lock()):
                    data = await context._write(claims, definition, args, account_id)
            elif definition.server == "artifact":
                data = await context._artifact(user_id, run_id, name.split(".")[1], args)
            elif definition.server == "demo":
                data = {"message": "Real MCP transport is connected", "synthetic": True}
            else:
                data = await asyncio.wait_for(
                    context.adapter(user_id).call(definition.server, name.split(".")[1], args),
                    context.settings.tool_timeout,
                )
            if definition.name == "drive.export_file":
                artifact = context.workspace_file_service.import_export(user_id, run_id, data)
                data = {**data, "artifact": artifact}
            if definition.server in {"docs", "sheets", "slides"}:
                context.workspace_file_service.record(
                    user_id, run_id, definition.server, data, args
                )
                if data.get("partial"):
                    raise Denied(
                        "PARTIAL_CREATION",
                        "Google created the file but could not finish populating or verifying it. Inspect the partial file in the Google file library before retrying.",
                    )
            sources = context._sources(definition.server, data)
            result = ToolResult(
                data=data,
                sources=sources,
                has_more=bool(data.get("next_page_token")),
                next_page_token=data.get("next_page_token"),
                operation_id=uid(),
            )
        except Denied as exc:
            result = ToolResult(status="error", code=exc.code, warnings=[str(exc)])
        except (ValueError, ValidationError) as exc:
            result = ToolResult(
                status="error",
                code=getattr(exc, "code", "INVALID_ARGUMENT"),
                warnings=[str(exc)[:300]],
            )
        except TimeoutError:
            result = ToolResult(
                status="error", code="PROVIDER_UNAVAILABLE", warnings=["Tool deadline exceeded"]
            )
        except Exception as exc:
            # Adapter errors expose only their deliberately sanitized message/code.
            code = getattr(exc, "code", "PROVIDER_UNAVAILABLE")
            result = ToolResult(
                status="error",
                code=code,
                warnings=[str(exc)[:200] if hasattr(exc, "code") else "Provider operation failed"],
            )
        if run_id:
            context.emit(
                run_id,
                "tool.completed",
                {
                    "tool": name,
                    "server": definition.server,
                    "status": result.status,
                    "code": result.code,
                    "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                    "sources": [{**s.model_dump(), "snippet": ""} for s in result.sources],
                    "operation_id": result.operation_id,
                    "data": {
                        "summary": "Retrieved authorized records"
                        if result.status == "success"
                        else result.warnings
                    },
                },
            )
        logging.getLogger("workspace.tools").info(
            json.dumps(
                {
                    "run_id": run_id,
                    "server": definition.server,
                    "tool": name,
                    "status": result.status,
                    "code": result.code,
                    "operation_id": result.operation_id,
                    "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                }
            )
        )
        return result
