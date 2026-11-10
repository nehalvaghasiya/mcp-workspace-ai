from __future__ import annotations

from typing import Any

from mcp_workspace_api.agents.summarizer import summarize
from mcp_workspace_api.core.security import Denied


def resolve(
    arguments: dict[str, Any], results: list[dict[str, Any]], previous: dict[str, Any]
) -> dict[str, Any]:
    values = dict(previous.get("references", {}))
    for item in results:
        data = item.get("data", {})
        for key, target in (("messages", "message"), ("events", "event"), ("files", "file")):
            records = data.get(key, [])
            if records:
                first = records[0]
                values[target] = first.get(target + "_id") or first.get("id")
                if key == "messages":
                    values["thread"] = first.get("thread_id")
        for key, target in (
            ("draft_id", "draft"),
            ("thread_id", "thread"),
            ("message_id", "message"),
            ("event_id", "event"),
        ):
            if data.get(key):
                values[target] = data[key]
        if data.get("format") and data.get("id"):
            values["artifact"] = data["id"]
    values["summary"] = summarize(results)
    output = dict(arguments)
    for key, value in output.items():
        if isinstance(value, str) and value.startswith("$"):
            value = values.get(value[1:])
            if value is None:
                if any(
                    item.get("tool") in {"gmail.search_messages", "drive.search_files"}
                    and not item.get("data", {}).get(
                        "messages", item.get("data", {}).get("files", [])
                    )
                    for item in results
                ):
                    raise Denied("RESOURCE_NOT_FOUND", "No matching source records were found")
                raise Denied(
                    "CLARIFICATION_REQUIRED", "Select the exact source or draft before continuing"
                )
            output[key] = value
    return output
