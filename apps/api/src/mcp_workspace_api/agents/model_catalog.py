"""Keep unrelated connector schemas out of ordinary single-service requests."""

from __future__ import annotations

import re
from typing import Any

HINTS = {
    "gmail": r"\b(gmail|inbox|email|emails|mail|message|messages|reply|draft)\b",
    "calendar": r"\b(calendar|calendars|meeting|meetings|schedule|scheduling|availability|freebusy)\b",
    "drive": r"\b(drive|folder|folders|file|files|document|documents)\b",
    "docs": r"\b(google docs?|document|documents)\b",
    "sheets": r"\b(google sheets?|spreadsheet|spreadsheets)\b",
    "slides": r"\b(google slides?|presentation|presentations)\b",
    "artifact": r"\b(pdf|word|docx|xlsx|pptx|csv|markdown|html|download|downloadable|report|brief|powerpoint|excel)\b",
}


def full_selection_read(results: list[dict[str, Any]]) -> bool:
    selected: set[str] | None = None
    read: set[str] = set()
    for item in results:
        data = item.get("data", {})
        if item.get("tool") == "gmail.search_messages":
            selected = {row["id"] for row in data.get("messages", [])}
        if item.get("tool") in {"gmail.get_message", "gmail.get_messages", "gmail.get_thread"}:
            read.update(row["id"] for row in data.get("messages", [data]) if row.get("id"))
    return selected is not None and selected <= read


def model_catalog(
    catalog: list[dict[str, Any]],
    prompt: str,
    history: list[dict[str, Any]],
    results: list[dict[str, Any]],
    previous: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    text = " ".join(
        [row["content"] for row in history[-4:] if row.get("role") == "user"] + [prompt]
    ).lower()
    namespaces = {name for name, pattern in HINTS.items() if re.search(pattern, text)}
    if not namespaces:
        namespaces = {row["tool"].split(".")[0] for row in (results or previous) if row.get("tool")}
    if (
        namespaces == {"gmail"}
        and re.search(r"\b(summarize|summary|summaries|prioritize|prioritized|decisions)\b", text)
        and not re.search(r"\b(send|draft|reply|archive|delete|trash|label|attachment)\b", text)
        and full_selection_read(results or previous)
    ):
        # The requested reads are complete. Synthesis needs evidence, not more tools.
        return []
    return [
        row
        for row in catalog
        if row["enabled"] and (not namespaces or row["name"].split(".")[0] in namespaces)
    ]
