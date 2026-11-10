from __future__ import annotations

import asyncio
from typing import Any

import httpx


async def smoke(url: str) -> dict[str, Any]:
    def require(condition: bool, message: str) -> None:
        if not condition:
            raise RuntimeError(message)

    async with httpx.AsyncClient(base_url=url, timeout=90) as client:
        require((await client.get("/api/health")).status_code == 200, "API health failed")
        session = (await client.post("/api/auth/demo")).json()
        client.headers["X-CSRF-Token"] = session["csrf_token"]
        catalog = (await client.get("/api/mcp/tools")).json()
        require(isinstance(catalog, list) and len(catalog) >= 31, "MCP discovery is incomplete")
        conversation = (await client.post("/api/conversations", json={})).json()
        run = (
            await client.post(
                f"/api/conversations/{conversation['id']}/messages",
                json={
                    "content": "Review Northstar launch emails, calendar meetings and Drive proposal; create PDF Word Excel PowerPoint reports."
                },
            )
        ).json()
        for _ in range(600):
            data = (await client.get(f"/api/conversations/{conversation['id']}")).json()
            state = next(row for row in data["runs"] if row["id"] == run["id"])
            if state["status"] in {"completed", "failed", "needs_approval"}:
                break
            await asyncio.sleep(0.1)
        require(state["status"] == "completed", "Mock workflow failed: " + str(state.get("error")))
        files = (await client.get("/api/artifacts")).json()
        require(
            {row["format"] for row in files} >= {"docx", "pdf", "xlsx", "pptx"},
            "Expected four artifact formats",
        )
        for row in files:
            downloaded = await client.get(row["download_url"])
            require(
                downloaded.status_code == 200 and len(downloaded.content) == row["size"],
                "Artifact download failed",
            )
        trace = (await client.get(f"/api/runs/{run['id']}/trace")).json()
        require(
            {row["server"] for row in trace} >= {"gmail", "calendar", "drive", "artifact"},
            "The workflow did not cross all four MCP servers",
        )
        return {
            "status": "PASS",
            "mode": "mock",
            "tools": len(catalog),
            "files": len(files),
            "trace_events": len(trace),
        }
