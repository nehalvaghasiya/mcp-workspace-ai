from __future__ import annotations

import asyncio
import json
import platform
import statistics
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

import httpx

from mcp_workspace_evaluations.case_loader import cases


async def evaluate(url: str, output: Path, categories: set[str] | None = None) -> dict[str, Any]:
    records = []
    for case in cases():
        if categories is not None and case["category"] not in categories:
            continue
        started = time.perf_counter()
        async with httpx.AsyncClient(base_url=url, timeout=60) as client:
            response = await client.post("/api/auth/demo")
            response.raise_for_status()
            identity = response.json()
            if identity["mode"] != "mock":
                raise ValueError("Deterministic evaluation requires mock mode")
            client.headers["X-CSRF-Token"] = identity["csrf_token"]
            settings = (await client.get("/api/settings")).json()
            if settings["provider"] != "fake":
                raise ValueError("Deterministic evaluation requires FakeLLM")
            conversation = (await client.post("/api/conversations", json={})).json()
            run = (
                await client.post(
                    f"/api/conversations/{conversation['id']}/messages",
                    json={"content": case["user_prompt"]},
                )
            ).json()
            for _ in range(600):
                snapshot = (await client.get(f"/api/conversations/{conversation['id']}")).json()
                actual = next(row for row in snapshot["runs"] if row["id"] == run["id"])
                if actual["status"] not in {"running", "queued"}:
                    break
                await asyncio.sleep(0.05)
            traces = (await client.get(f"/api/runs/{run['id']}/trace")).json()
            tools = [row["tool"] for row in traces if row["type"] == "tool.completed"]
            artifacts = (await client.get("/api/artifacts")).json()
            answer: dict[str, Any] = next(
                (row for row in reversed(snapshot["messages"]) if row["role"] == "assistant"), {}
            )
            sources = answer.get("sources", [])
            returned_refs = {
                (source["provider"], source["resource_id"])
                for row in traces
                for source in row.get("sources", [])
            }
            assertions = {
                "state": actual["status"] == case["expected_state"],
                "tools": set(case["expected_tools"]) <= set(tools),
                "no_unapproved_writes": not (set(case["forbidden_tools"]) & set(tools)),
                "artifact_formats": set(case["expected_artifact_formats"])
                <= {row["format"] for row in artifacts},
                "artifact_validity": all(row["validated"] and row["size"] > 0 for row in artifacts),
                "evidence": set(case["required_evidence"])
                <= {source["provider"] for source in sources},
                "citation_integrity": all(
                    (source["provider"], source["resource_id"]) in returned_refs
                    for source in sources
                ),
            }
            for artifact in artifacts:
                download = await client.get(artifact["download_url"])
                import hashlib

                assertions["artifact_validity"] = (
                    assertions["artifact_validity"]
                    and download.status_code == 200
                    and hashlib.sha256(download.content).hexdigest() == artifact["sha256"]
                )
            relevant = [name for name in tools if name != "demo.ping"]
            required = set(case["expected_tools"])
            records.append(
                {
                    **case,
                    "actual_state": actual["status"],
                    "passed": all(assertions.values()),
                    "assertions": assertions,
                    "tools": tools,
                    "tool_precision": sum(name in required for name in relevant) / len(relevant)
                    if relevant and required
                    else None,
                    "tool_recall": len(required & set(tools)) / len(required) if required else None,
                    "source_refs_checked": len(sources),
                    "artifacts_checked": len(artifacts),
                    "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                    "error": actual.get("error"),
                }
            )
            if actual["status"] == "needs_approval":
                await client.post(f"/api/runs/{run['id']}/cancel")
            await client.delete("/api/account")
    durations = sorted(row["elapsed_ms"] for row in records)
    report = {
        "kind": "deterministic routing pipeline test",
        "measured_at": datetime.now(UTC).isoformat(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "mcp": version("mcp"),
            "protocol": "2026-07-28",
            "model": "FakeLLM",
            "fixture": "northstar-1",
        },
        "cases": len(records),
        "passed": sum(row["passed"] for row in records),
        "latency_ms": {
            "p50": statistics.median(durations),
            "p95": durations[int((len(durations) - 1) * 0.95)],
        },
        "source_groundedness": "citation reference integrity only; freeform claim accuracy NOT_RUN",
        "model_cost": 0,
        "real_model_evaluation": "NOT_RUN",
        "live_google": "NOT_RUN",
        "records": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(output.write_text, json.dumps(report, indent=2) + "\n")
    output.with_suffix(".md").write_text(
        f"# Deterministic pipeline results\n\nMeasured {report['measured_at']}. FakeLLM with synthetic data, not model reasoning accuracy.\n\n{report['passed']}/{report['cases']} expected workflow states.\n\np50 {report['latency_ms']['p50']:.1f} ms; p95 {report['latency_ms']['p95']:.1f} ms.\n\nLive Google and real-model evaluation: NOT_RUN.\n"
    )
    return {key: value for key, value in report.items() if key != "records"}
