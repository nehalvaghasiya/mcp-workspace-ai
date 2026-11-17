from __future__ import annotations

from typing import Any

import pytest
from mcp_workspace_api.contracts import ToolResult
from mcp_workspace_api.db import User
from mcp_workspace_api.mcp.registry import tool_definitions
from mcp_workspace_api.operations.live_verification import verify_live

from tests.support import Browser, LiveServer


async def test_live_verification_uses_valid_read_requests_for_every_service(
    live_server: LiveServer,
    browser: Browser,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = live_server.runtime
    monkeypatch.setattr(runtime.settings, "mode", "live")
    monkeypatch.setattr(runtime.settings, "llm_provider", "openai_compatible")
    with runtime.db.session() as session:
        user = session.get(User, browser.user_id)
        assert user is not None
        user.subject = "https://accounts.google.com:synthetic-verification"
    requested: list[str] = []
    definitions = tool_definitions("live")

    async def invoke(user_id: str, tool: str, arguments: dict[str, Any]) -> ToolResult:
        assert user_id == browser.user_id
        definitions[tool].input_model.model_validate(arguments)
        requested.append(tool)
        return ToolResult(data={"files": [{"id": "synthetic-file"}]})

    async def complete(*args: Any, **kwargs: Any) -> dict[str, Any]:
        body = args[2]
        assert "synthetic-verification" not in str(body)
        if "tools" in body:
            return {
                "choices": [
                    {
                        "message": {
                            "tool_calls": [{"function": {"name": "workspace_connection_check"}}]
                        }
                    }
                ]
            }
        return {"choices": [{"message": {"content": "Hello"}}]}

    monkeypatch.setattr(runtime, "invoke", invoke)
    monkeypatch.setattr("mcp_workspace_api.operations.live_verification.completion", complete)
    result = await verify_live(runtime)
    assert result["status"] == "PASS"
    assert set(result["google"]) == {"gmail", "calendar", "drive", "docs", "sheets", "slides"}
    assert "docs.get_document" in requested and "sheets.get_spreadsheet" in requested
    assert "slides.get_presentation" in requested
