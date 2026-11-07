from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import httpx
import pytest


@dataclass
class Browser:
    http: httpx.AsyncClient
    user_id: str
    csrf: str

    async def conversation(self, title: str = "Integration test") -> str:
        response = await self.http.post("/api/conversations", json={"title": title})
        assert response.status_code == 200, response.text
        return str(response.json()["id"])

    async def start(
        self, prompt: str, conversation: str | None = None, request_id: str | None = None
    ) -> tuple[str, str]:
        conversation = conversation or await self.conversation()
        response = await self.http.post(
            f"/api/conversations/{conversation}/messages",
            json={"content": prompt, "request_id": request_id or uuid4().hex},
        )
        assert response.status_code == 200, response.text
        return conversation, str(response.json()["id"])

    async def wait(
        self,
        conversation: str,
        run_id: str,
        *,
        statuses: set[str] | None = None,
        deadline_seconds: float = 25,
    ) -> dict[str, Any]:
        statuses = statuses or {"completed", "failed", "cancelled", "needs_approval", "interrupted"}
        deadline = time.monotonic() + deadline_seconds
        payload: dict[str, Any] = {}
        while time.monotonic() < deadline:
            response = await self.http.get(f"/api/conversations/{conversation}")
            assert response.status_code == 200, response.text
            payload = response.json()
            for run in payload["runs"]:
                if run["id"] == run_id and run["status"] in statuses:
                    return dict(run)
            await asyncio.sleep(0.025)
        pytest.fail(f"Run did not reach {statuses}: {payload}")
