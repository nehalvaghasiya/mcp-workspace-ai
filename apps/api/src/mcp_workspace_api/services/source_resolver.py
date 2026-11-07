from __future__ import annotations

from typing import Any

from mcp_workspace_api.contracts import (
    SourceRef,
)
from mcp_workspace_api.core.presenters import timestamp


def resolve_sources(server: str, data: dict[str, Any]) -> list[SourceRef]:
    if server not in {"gmail", "calendar", "drive"}:
        return []
    supplied = data.get("sources", [])
    if supplied:
        return [
            SourceRef(
                provider=server,
                resource_id=str(source["resource_id"]),
                title=str(source["title"]),
                url=source.get("url"),
                retrieved_at=timestamp(),
                snippet=str(source.get("snippet") or "")[:200],
                pointer=str(source.get("pointer") or ""),
            )
            for source in supplied[:50]
        ]
    records: list[dict[str, Any]] = []
    for key in ("messages", "events", "files"):
        if isinstance(data.get(key), list):
            records.extend(data[key])
    if not records:
        records = [data]
    sources: list[SourceRef] = []
    for row in records[:50]:
        rid = (
            row.get("message_id")
            or row.get("event_id")
            or row.get("file_id")
            or row.get("id")
            or row.get("thread_id")
        )
        if rid:
            sources.append(
                SourceRef(
                    provider=server,
                    resource_id=str(rid),
                    title=str(row.get("subject") or row.get("title") or row.get("name") or rid),
                    url=row.get("web_url") or row.get("webViewLink") or row.get("htmlLink"),
                    retrieved_at=timestamp(),
                    snippet=str(row.get("snippet") or "")[:200],
                    pointer=str(row.get("offset", "")),
                )
            )
    return sources
