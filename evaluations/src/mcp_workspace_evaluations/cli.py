"""Shared subset runner; the full workspace-ai eval command preserves all 52 cases."""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from mcp_workspace_evaluations.runner import evaluate


def main(categories: set[str], name: str) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("API_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--output", type=Path, default=Path(f"evaluations/reports/{name}.json"))
    args = parser.parse_args()
    report = asyncio.run(evaluate(args.url, args.output, categories))
    print(f"{report['passed']}/{report['cases']} deterministic cases passed")
    if report["passed"] != report["cases"]:
        raise SystemExit(1)
