"""Capture genuine synthetic artifacts and a redacted trace from the running mock app."""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

import httpx
from mcp_documents.artifacts import ArtifactEngine


async def generate(url: str = "http://127.0.0.1:8000") -> None:
    async with httpx.AsyncClient(base_url=url, timeout=60) as client:
        response = await client.post("/api/auth/demo")
        response.raise_for_status()
        identity = response.json()
        if identity["mode"] != "mock":
            raise RuntimeError("Synthetic example capture requires mock mode")
        client.headers["X-CSRF-Token"] = identity["csrf_token"]
        conversation = (await client.post("/api/conversations", json={})).json()
        run = (
            await client.post(
                f"/api/conversations/{conversation['id']}/messages",
                json={
                    "content": "Review launch emails, calendar meetings and Drive proposal; create PDF Word Excel PowerPoint reports."
                },
            )
        ).json()
        for _ in range(600):
            state = (await client.get(f"/api/conversations/{conversation['id']}")).json()
            current = next(row for row in state["runs"] if row["id"] == run["id"])
            if current["status"] in {"completed", "failed"}:
                break
            await asyncio.sleep(0.1)
        if current["status"] != "completed":
            raise RuntimeError("Synthetic example workflow failed")
        directory = Path("examples/document-generation/generated")
        await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
        manifest = []
        for artifact in (await client.get("/api/artifacts")).json():
            response = await client.get(artifact["download_url"])
            response.raise_for_status()
            if hashlib.sha256(response.content).hexdigest() != artifact["sha256"]:
                raise RuntimeError("Download checksum mismatch")
            path = directory / ("northstar-launch." + artifact["format"])
            await asyncio.to_thread(path.write_bytes, response.content)
            validation = ArtifactEngine().validate(path, artifact["format"])
            manifest.append(
                {
                    "file": path.name,
                    "size": len(response.content),
                    "sha256": artifact["sha256"],
                    "validation": validation,
                    "sources": artifact["sources"],
                }
            )
        await asyncio.to_thread(
            (directory / "manifest.json").write_text, json.dumps(manifest, indent=2) + "\n"
        )
        trace = (await client.get(f"/api/runs/{run['id']}/trace")).json()
        proof = Path("examples/multi-server-workflows/expected-traces/northstar.json")
        proof.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(
            proof.write_text, json.dumps({"synthetic": True, "trace": trace}, indent=2) + "\n"
        )
        await client.delete("/api/account")
        print(f"Captured and reopened {len(manifest)} synthetic artifacts with a real MCP trace.")


if __name__ == "__main__":
    asyncio.run(generate())
