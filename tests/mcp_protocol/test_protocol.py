"""Official SDK clients exercise real Streamable HTTP and subprocess stdio."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import httpx
import pytest
from mcp import Client, MCPError, StdioServerParameters
from mcp.types import TextContent, TextResourceContents

from tests.support import Browser, LiveServer

READ_CALLS: list[tuple[str, dict[str, Any]]] = [
    ("gmail.search_messages", {"query": "launch", "max_results": 2}),
    ("gmail.get_message", {"message_id": "msg-001"}),
    ("gmail.get_thread", {"thread_id": "thread-01"}),
    ("gmail.list_labels", {}),
    ("calendar.list_calendars", {}),
    (
        "calendar.list_events",
        {"time_min": "2026-11-05T00:00:00-06:00", "time_max": "2026-12-01T00:00:00-06:00"},
    ),
    ("calendar.get_event", {"event_id": "event-001"}),
    (
        "calendar.query_freebusy",
        {
            "calendar_ids": ["primary"],
            "time_min": "2026-11-05T00:00:00-06:00",
            "time_max": "2026-11-06T00:00:00-06:00",
        },
    ),
    ("drive.search_files", {"query": "launch", "max_results": 2}),
    ("drive.get_file_metadata", {"file_id": "proposal"}),
    ("drive.read_file", {"file_id": "proposal", "max_chars": 100}),
    ("drive.list_folder", {"folder_id": "root"}),
    ("demo.ping", {}),
]


async def call(client: Client, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    result = await client.call_tool(name, {"request": arguments})
    assert result.is_error is False, result
    assert isinstance(result.structured_content, dict), result
    return result.structured_content


async def assert_rejected(client: Client, name: str, arguments: dict[str, Any]) -> None:
    try:
        result = await client.call_tool(name, arguments)
    except MCPError:
        return
    assert result.is_error or (result.structured_content or {}).get("status") == "error", result


@pytest.mark.parametrize("namespace", ["gmail", "calendar", "drive", "artifact", "demo"])
async def test_http_tool_resource_prompt_discovery(
    live_server: LiveServer, browser: Browser, namespace: str
) -> None:
    async with live_server.mcp(browser.user_id, namespace) as client:
        assert client.protocol_version == "2026-07-28"
        listing = await client.list_tools()
        expected = {name for name in live_server.runtime.tools if name.startswith(namespace + ".")}
        assert {tool.name for tool in listing.tools} == expected
        for tool in listing.tools:
            assert tool.input_schema["type"] == "object"
            assert "request" in tool.input_schema["properties"]
            assert tool.output_schema
        resources = await client.list_resources()
        assert resources.resources
        resource = await client.read_resource(str(resources.resources[0].uri))
        resource_content = resource.contents[0]
        assert isinstance(resource_content, TextResourceContents)
        assert "business_report" in resource_content.text
        prompts = await client.list_prompts()
        assert any(prompt.name == "meeting_brief" for prompt in prompts.prompts)
        prompt = await client.get_prompt("meeting_brief", {"topic": "Synthetic launch"})
        prompt_content = prompt.messages[0].content
        assert isinstance(prompt_content, TextContent)
        assert "Synthetic launch" in prompt_content.text


@pytest.mark.parametrize("name,arguments", READ_CALLS, ids=[row[0] for row in READ_CALLS])
async def test_all_provider_reads_over_real_http(
    live_server: LiveServer, browser: Browser, name: str, arguments: dict[str, Any]
) -> None:
    async with live_server.mcp(browser.user_id, name.split(".")[0]) as client:
        result = await call(client, name, arguments)
    assert result["status"] == "success", result
    assert result["data"]
    if name in {"gmail.search_messages", "drive.search_files"}:
        assert result["sources"]
        assert all(source["resource_id"] for source in result["sources"])


async def test_every_registered_schema_rejects_unknown_arguments_without_effects(
    live_server: LiveServer, browser: Browser
) -> None:
    definitions = live_server.runtime.tools
    assert len(definitions) == 31
    before = live_server.runtime.adapter(browser.user_id)._load()
    for namespace in ("gmail", "calendar", "drive", "artifact", "demo"):
        async with live_server.mcp(browser.user_id, namespace) as client:
            for name in definitions:
                if name.startswith(namespace + "."):
                    await assert_rejected(
                        client, name, {"request": {"unrecognized_parameter": "../../etc/passwd"}}
                    )
    assert live_server.runtime.adapter(browser.user_id)._load() == before
    assert (await browser.http.get("/api/artifacts")).json() == []


@pytest.mark.parametrize("format", ["docx", "pdf", "xlsx", "pptx", "csv", "markdown", "html"])
async def test_every_artifact_tool_and_metadata_over_protocol(
    live_server: LiveServer, browser: Browser, format: str
) -> None:
    async with live_server.mcp(browser.user_id, "artifact") as client:
        rendered = await call(
            client,
            "artifact.create_" + format,
            {
                "format": format,
                "title": "Protocol café report",
                "blocks": [{"type": "paragraph", "text": "Synthetic budget: €42"}],
            },
        )
        assert rendered["status"] == "success", rendered
        artifact = rendered["data"]
        assert artifact["format"] == format and artifact["validated"]
        metadata = await call(
            client, "artifact.get_artifact_metadata", {"artifact_id": artifact["id"]}
        )
        assert metadata["data"]["sha256"] == artifact["sha256"]
        listed = await call(client, "artifact.list_artifacts", {"max_results": 10})
        assert any(row["id"] == artifact["id"] for row in listed["data"]["artifacts"])
        validated = await call(
            client, "artifact.validate_artifact", {"artifact_id": artifact["id"]}
        )
        assert validated["status"] == "success", validated
        assert validated["data"]["validation"]["valid"]


async def test_http_auth_expiry_audience_origin_and_spoofed_user(
    live_server: LiveServer, browser: Browser
) -> None:
    claims = {"user_id": browser.user_id, "server": "demo", "tools": ["demo.ping"]}
    cases = [
        ({}, 401),
        ({"Authorization": "Bearer invalid"}, 401),
        ({"Authorization": "Bearer " + live_server.runtime.signer.issue(claims, ttl=-1)}, 401),
        (
            {
                "Authorization": "Bearer "
                + live_server.runtime.signer.issue({**claims, "server": "gmail"})
            },
            401,
        ),
        (
            {
                "Authorization": "Bearer "
                + live_server.runtime.signer.issue({**claims, "user_id": "unavailable-user"})
            },
            401,
        ),
        (
            {
                "Authorization": "Bearer " + live_server.runtime.signer.issue(claims),
                "Origin": "https://attacker.invalid",
            },
            403,
        ),
    ]
    async with httpx.AsyncClient(base_url=live_server.url) as http:
        for headers, expected_status in cases:
            response = await http.post(
                "/mcp/demo/",
                headers=headers,
                json={"jsonrpc": "2.0", "id": 1, "method": "server/discover"},
            )
            assert response.status_code == expected_status, response.text
    async with live_server.mcp(browser.user_id, "demo", tools=["read"]) as client:
        await assert_rejected(client, "demo.ping", {"request": {}})
    async with live_server.mcp(browser.user_id, "demo", tools=["demo.unknown"]) as client:
        await assert_rejected(client, "demo.unknown", {"request": {}})


async def test_artifact_ownership_is_enforced_inside_mcp(
    live_server: LiveServer, browser: Browser
) -> None:
    async with live_server.mcp(browser.user_id, "artifact") as client:
        rendered = await call(
            client, "artifact.create_pdf", {"format": "pdf", "title": "Private owner report"}
        )
    artifact_id = rendered["data"]["id"]
    async with live_server.browser() as other:
        async with live_server.mcp(other.user_id, "artifact") as client:
            result = await call(
                client, "artifact.get_artifact_metadata", {"artifact_id": artifact_id}
            )
            assert result["status"] == "error"
            assert result["code"] == "RESOURCE_NOT_FOUND"


async def test_real_stdio_subprocess_discovery_and_call(
    live_server: LiveServer, browser: Browser, tmp_path: Path
) -> None:
    executable = shutil.which("uv")
    assert executable is not None, "uv is required for the documented stdio entrypoint"
    token = live_server.runtime.signer.issue(
        {"user_id": browser.user_id, "server": "demo", "tools": ["demo.ping"]}
    )
    env = {
        "MODE": "mock",
        "DATA_DIR": str(live_server.settings.data_dir),
        "API_URL": live_server.url,
        "WORKSPACE_MCP_TOKEN": token,
        "SESSION_SECRET": live_server.settings.session_secret,
        "TOKEN_ENCRYPTION_KEY": live_server.settings.token_encryption_key,
        "LLM_PROVIDER": "fake",
        "UV_NO_SYNC": "1",
        "UV_OFFLINE": "1",
        "UV_CACHE_DIR": "/tmp/workspace-ai-uv-cache",
        "PATH": os.environ.get("PATH", ""),
    }
    parameters = StdioServerParameters(
        command=executable,
        args=["run", "workspace-ai", "mcp", "demo", "--transport", "stdio"],
        env=env,
        cwd=Path(__file__).parents[1],
    )
    async with Client(parameters, read_timeout_seconds=15) as client:
        assert client.protocol_version == "2026-07-28"
        assert "demo.ping" in {tool.name for tool in (await client.list_tools()).tools}
        result = await call(client, "demo.ping", {})
        assert result["status"] == "success"
        assert result["data"]["synthetic"] is True
