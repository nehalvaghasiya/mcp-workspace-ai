"""Bound model context structurally, retaining complete tool-call/result pairs."""

from __future__ import annotations

import json
from typing import Any


def project(value: Any, text_limit: int = 12000, depth: int = 0) -> Any:
    if depth > 16:
        return {"truncated": True}
    if isinstance(value, str):
        return value if len(value) <= text_limit else value[:text_limit] + "\n[Content truncated]"
    if isinstance(value, list):
        return [project(item, text_limit, depth + 1) for item in value[:100]]
    if isinstance(value, dict):
        result = {
            key: project(item, text_limit, depth + 1)
            for key, item in value.items()
            if key not in {"raw", "body_html"}
            and not (key == "text" and value.get("body_text") == item)
            and not (key == "sources" and depth > 1)
        }
        if any(isinstance(item, str) and len(item) > text_limit for item in value.values()):
            result["truncated"] = True
        return result
    return value


def evidence_json(results: list[dict[str, Any]], budget: int = 120000) -> str:
    """Keep every selected record; reduce field lengths rather than cut JSON."""
    limit = 12000
    while True:
        payload = json.dumps(project(results, limit), ensure_ascii=False)
        if len(payload) <= budget:
            return payload
        if limit <= 128:
            return json.dumps(
                [
                    {
                        "truncated": True,
                        "omitted_results": len(results),
                        "warning": "Evidence structure exceeded the context budget; retrieve a smaller selection.",
                    }
                ]
            )
        limit //= 2


def paired_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[list[dict[str, Any]]] = []
    for index, message in enumerate(messages):
        if message.get("role") != "assistant" or not message.get("tool_calls"):
            continue
        calls = message["tool_calls"]
        following = messages[index + 1 : index + 1 + len(calls)]
        if {row.get("tool_call_id") for row in following if row.get("role") == "tool"} != {
            call["id"] for call in calls
        }:
            continue
        clean = []
        for row in following:
            try:
                content = json.loads(row["content"])
            except (ValueError, TypeError):
                content = {"truncated": True, "warning": "Older saved evidence was incomplete"}
            clean.append({**row, "content": evidence_json([content], 60000)[1:-1]})
        groups.append([message, *clean])
    return [row for group in groups[-24:] for row in group]
