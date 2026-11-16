"""Read checkpoints are reusable; effects and incomplete tool calls are not replayed."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from mcp_workspace_api.contracts import Risk
from mcp_workspace_api.db import Run, RunEvent

if TYPE_CHECKING:
    from mcp_workspace_api.core.execution_context import Runtime

MODEL_FAILURES = {
    "MODEL_TIMED_OUT",
    "MODEL_RATE_LIMITED",
    "MODEL_INVALID_RESPONSE",
    "MODEL_AUTH_REQUIRED",
    "PROVIDER_UNAVAILABLE",
}


def recovery_details(runtime: Runtime, run: Run) -> dict[str, Any]:
    state = run.state or {}
    code = state.get("error_code")
    if not code and run.status in {"failed", "interrupted"}:
        with runtime.db.session() as session:
            event = session.scalar(
                select(RunEvent)
                .where(RunEvent.run_id == run.id, RunEvent.type == "run.failed")
                .order_by(RunEvent.sequence.desc())
                .limit(1)
            )
            code = event.data.get("code") if event else None
    results = state.get("results", [])
    safe = all(
        row.get("tool") in runtime.tools
        and runtime.tools[row["tool"]].risk == Risk.READ
        and row.get("status", "success") == "success"
        for row in results
    )
    # Legacy model timeouts also identify a safe model boundary.
    phase = state.get("phase") or ("model" if code == "MODEL_TIMED_OUT" else None)
    read_ids: set[str] = set()
    selected: int | None = None
    sources: dict[tuple[str, str], Any] = {}
    for row in results:
        data = row.get("data", {})
        if row.get("tool") == "gmail.search_messages":
            selected = len(data.get("messages", []))
        if row.get("tool") in {"gmail.get_message", "gmail.get_messages", "gmail.get_thread"}:
            for item in data.get("messages", [data]):
                if item.get("id"):
                    read_ids.add(item["id"])
        for source in row.get("sources", []):
            sources[(source["provider"], source["resource_id"])] = source
    return {
        "error_code": code,
        "retryable": run.status in {"failed", "interrupted"}
        and code in MODEL_FAILURES
        and phase == "model"
        and safe
        and not state.get("pending_step"),
        "retry_of": state.get("retry_of"),
        "read_count": len(read_ids),
        "selected_count": selected,
        "sources": list(sources.values()) if run.status in {"failed", "interrupted"} else [],
    }
