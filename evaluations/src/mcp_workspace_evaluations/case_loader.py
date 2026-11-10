from __future__ import annotations

import json
from importlib.resources import files
from typing import Any


def cases() -> list[dict[str, Any]]:
    root = files("mcp_workspace_evaluations").joinpath("datasets")
    records = [
        json.loads(line)
        for path in root.iterdir()
        if path.name.endswith(".jsonl")
        for line in path.read_text().splitlines()
        if line.strip()
    ]
    order = {
        name: index
        for index, name in enumerate(
            ("gmail", "calendar", "drive", "artifacts", "cross_app", "approvals", "impossible")
        )
    }
    records.sort(key=lambda row: (order[row["category"]], row["case_id"]))
    return records
