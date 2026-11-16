"""Canned artifact content for the isolated synthetic fixture."""

from __future__ import annotations

import re
from typing import Any

from mcp_workspace_api.agents.summarizer import summarize


def artifact_content(args: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    text = summarize(results)
    if text.startswith("No matching"):
        text = "Synthetic example report. No external source facts were requested."
    content = {**args, "blocks": [], "sheets": [], "slides": []}
    if args["format"] in {"xlsx", "csv"}:
        source_sheets = [
            {
                "name": "Sources",
                "columns": ["Source", "Summary"],
                "rows": [
                    [
                        {"type": "string", "value": source["resource_id"]},
                        {"type": "string", "value": source["title"]},
                    ]
                    for result in results
                    for source in result.get("sources", [])
                ][:1000]
                or [
                    [
                        {"type": "string", "value": "Demo"},
                        {"type": "string", "value": "Synthetic example"},
                    ]
                ],
            }
        ]
        task_rows: list[list[dict[str, str]]] = []
        seen_tasks: set[tuple[str, str]] = set()
        for result in results:
            data = result.get("data", {})
            records = data.get("messages", []) or [data]
            for record in records:
                body = str(
                    record.get("body_text") or record.get("text") or record.get("content") or ""
                )
                source = str(
                    record.get("message_id") or record.get("file_id") or record.get("id") or ""
                )
                for owner, task in re.findall(
                    r"\b([A-Z][a-z]+) owns (?:the )?([a-z]+(?: [a-z]+)?)(?=[.;,\n]|$)", body
                ):
                    if (owner, task) not in seen_tasks:
                        seen_tasks.add((owner, task))
                        task_rows.append(
                            [
                                {"type": "string", "value": value}
                                for value in (task, owner, "", source)
                            ]
                        )
        if task_rows:
            content["sheets"] = [
                {
                    "name": "Tasks",
                    "columns": ["Task", "Owner", "Due date (unspecified)", "Source"],
                    "rows": task_rows,
                }
            ]
            if args["format"] == "xlsx":
                content["sheets"].extend(source_sheets)
        else:
            content["sheets"] = source_sheets
    elif args["format"] == "pptx":
        content["slides"] = [
            {
                "title": title,
                "body": text[:900]
                if index == 1
                else "Based on the source records listed in this report.",
                "bullets": [],
            }
            for index, title in enumerate(
                [
                    "Northstar launch",
                    "Source evidence",
                    "Meetings and conflicts",
                    "Risks and decisions",
                    "Next steps",
                ]
            )
        ]
    else:
        content["blocks"] = [
            {"type": "heading", "level": 1, "text": "Decision brief"},
            {"type": "paragraph", "text": text[:9000]},
            {
                "type": "bullet_list",
                "items": ["Review the cited source records", "Confirm outstanding decisions"],
            },
        ]
    sources = list(
        {
            (source["provider"], source["resource_id"]): source
            for item in results
            for source in item.get("sources", [])
        }.values()
    )
    citations = [
        f"{source['provider']}:{source['resource_id']} - {source['title']}" for source in sources
    ]
    if citations and args["format"] not in {"xlsx", "csv", "pptx"}:
        content["blocks"].extend(
            [
                {"type": "heading", "level": 2, "text": "Sources"},
                {"type": "bullet_list", "items": citations[:50]},
            ]
        )
    if citations and args["format"] == "pptx":
        content["slides"][-1]["body"] = "Sources: " + "; ".join(citations)[:850]
    return content
