from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import httpx
import pytest
from mcp_workspace_api.connectors import (
    ConnectorError,
    GoogleWorkspace,
    MockWorkspace,
    synthetic_workspace,
)

from tests.support.connector_fixtures import token


async def test_drive_access_truncation_pagination_and_upload(
    workspace: MockWorkspace, tmp_path: Path
) -> None:
    result = await workspace.call("drive", "search_files", {"query": "Launch proposal"})
    assert len(result["files"]) == 2
    assert "drive.file" in result["scope_note"]
    for file_id in ["report-18", "report-21"]:
        with pytest.raises(ConnectorError, match="open or select"):
            await workspace.call("drive", "read_file", {"file_id": file_id})
    content = await workspace.call("drive", "read_file", {"file_id": "proposal", "max_chars": 30})
    assert content["truncated"] and len(content["text"]) == 30
    with pytest.raises(ConnectorError, match="Unsupported"):
        await workspace.call("drive", "read_file", {"file_id": "report-20"})
    path = tmp_path / "memo.txt"
    path.write_text("Synthetic memo")
    artifact = {
        "path": str(path),
        "title": "memo.txt",
        "mime_type": "text/plain",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    args = {"artifact_id": "owned-artifact", "folder_id": "folder-projects", "_artifact": artifact}
    snapshot = await workspace.snapshot("drive", "upload_artifact", args)
    uploaded = await workspace.call("drive", "upload_artifact", args | {"_snapshot": snapshot})
    assert uploaded["parents"] == ["folder-projects"]
    assert (await workspace.call("drive", "read_file", {"file_id": uploaded["id"]}))[
        "text"
    ] == "Synthetic memo"
    path.write_text("Changed")
    with pytest.raises(ConnectorError, match="changed"):
        await workspace.call("drive", "upload_artifact", args | {"_snapshot": snapshot})


async def test_mock_native_drive_files_and_metadata_minimization(workspace: MockWorkspace) -> None:
    for file_id in ["report-07", "report-08", "report-09"]:
        result = await workspace.call("drive", "read_file", {"file_id": file_id})
        assert "Synthetic launch" in result["text"]
        metadata = await workspace.call("drive", "get_file_metadata", {"file_id": file_id})
        assert "content_base64" not in metadata
    listing = await workspace.call("drive", "search_files", {"max_results": 100})
    assert all("content_base64" not in x and "content" not in x for x in listing["files"])
    nested = await workspace.call("drive", "list_folder", {"folder_id": "report-17"})
    assert [x["id"] for x in nested["files"]] == ["report-16"]


@pytest.mark.parametrize(
    "query,expected",
    [
        ("name contains 'Launch proposal' and trashed = false", ["proposal", "report-05"]),
        (
            "mimeType = 'application/vnd.google-apps.spreadsheet' and 'folder-projects' in parents",
            ["budget"],
        ),
        ("fullText contains 'vendor delay'", ["proposal", "slides"]),
    ],
)
async def test_mock_drive_query_operators(
    workspace: MockWorkspace, query: str, expected: list[str]
) -> None:
    result = await workspace.call("drive", "search_files", {"query": query})
    assert [x["id"] for x in result["files"]] == expected


async def test_live_drive_export_and_verified_multipart_upload(tmp_path: Path) -> None:
    from mcp_workspace_common.extraction import decode_base64url

    source = next(x for x in synthetic_workspace()["files"] if x["id"] == "report-08")
    data = decode_base64url(source["content_base64"])
    requests: list[httpx.Request] = []
    path = tmp_path / "artifact.xlsx"
    path.write_bytes(data)
    artifact = {
        "path": str(path),
        "title": "artifact.xlsx",
        "mime_type": source["mimeType"],
        "sha256": hashlib.sha256(data).hexdigest(),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "POST":
            assert request.url.params["uploadType"] == "multipart"
            assert "multipart/related" in request.headers["Content-Type"]
            assert data in request.content
            return httpx.Response(200, json={"id": "uploaded-1"})
        if request.url.path.endswith("/export"):
            assert request.url.params["mimeType"] == source["mimeType"]
            return httpx.Response(200, content=data)
        return httpx.Response(
            200,
            json={
                "id": "sheet-1",
                "name": "Budget",
                "mimeType": "application/vnd.google-apps.spreadsheet",
                "capabilities": {"canDownload": True},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        workspace = GoogleWorkspace(token, client)
        content = await workspace.call("drive", "read_file", {"file_id": "sheet-1"})
        assert "24000" in content["text"]
        uploaded = await workspace.call(
            "drive", "upload_artifact", {"artifact_id": "owned-1", "_artifact": artifact}
        )
        assert uploaded["id"] == "uploaded-1"
        assert len(requests) == 3


@pytest.mark.parametrize("tool", ["get_file_metadata", "read_file"])
async def test_live_drive_resource_key_header_survives_read_retries(tool: str) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["X-Goog-Drive-Resource-Keys"] == "selected-file/0-example_key-123"
        assert "resource_key" not in request.url.params
        if len(requests) == 1:
            return httpx.Response(429)
        if request.url.params.get("alt") == "media":
            return httpx.Response(200, content=b"Synthetic selected file")
        return httpx.Response(
            200,
            json={
                "id": "selected-file",
                "name": "Selected note",
                "mimeType": "text/plain",
                "size": "23",
                "capabilities": {"canDownload": True},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GoogleWorkspace(token, client).call(
            "drive", tool, {"file_id": "selected-file", "resource_key": "0-example_key-123"}
        )
        assert result["id"] == "selected-file"
        assert len(requests) == (3 if tool == "read_file" else 2)


async def test_live_drive_resource_key_forwarded_on_native_export() -> None:
    from mcp_workspace_api.connectors import _synthetic_binary
    from mcp_workspace_common.extraction import XLSX, decode_base64url

    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["X-Goog-Drive-Resource-Keys"] == "selected-sheet/0-key"
        if request.url.path.endswith("/export"):
            return httpx.Response(200, content=decode_base64url(_synthetic_binary(XLSX)))
        return httpx.Response(
            200,
            json={
                "id": "selected-sheet",
                "name": "Selected sheet",
                "mimeType": "application/vnd.google-apps.spreadsheet",
                "capabilities": {"canDownload": True},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GoogleWorkspace(token, client).call(
            "drive", "read_file", {"file_id": "selected-sheet", "resource_key": "0-key"}
        )
        assert "24000" in result["text"]
        assert len(requests) == 2


@pytest.mark.parametrize(
    "resource_key",
    [
        "",
        "x" * 301,
        "key\r\nAuthorization: attacker",
        "key,other-file/other-key",
        "key/slash",
        "non ascii é",
        {"bad": "type"},
    ],
)
async def test_drive_resource_key_rejects_header_injection_before_http(resource_key: Any) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ConnectorError) as caught:
            await GoogleWorkspace(token, client).call(
                "drive",
                "get_file_metadata",
                {"file_id": "selected-file", "resource_key": resource_key},
            )
        assert caught.value.code == "invalid_input"
        assert not requests
