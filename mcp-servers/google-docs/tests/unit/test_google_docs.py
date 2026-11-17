from __future__ import annotations

import copy
import json
from typing import Any

import httpx
import pytest
from mcp_google_docs.providers.content import document_body, text_requests
from mcp_google_docs.providers.google import GoogleDocs
from mcp_google_docs.schemas.create_document import CreateDocument
from mcp_google_docs.schemas.update_document import UpdateDocument
from mcp_google_docs.server import tool_definitions
from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.providers.google_client import GoogleClient
from pydantic import ValidationError


async def token() -> str:
    return "synthetic-token"


def document(text: str = "", revision: str = "revision1") -> dict[str, Any]:
    return {
        "documentId": "document1",
        "title": "Actual document",
        "revisionId": revision,
        "tabs": [
            {
                "tabProperties": {"tabId": "tab1"},
                "documentTab": {
                    "body": {
                        "content": [
                            {
                                "startIndex": 1,
                                "endIndex": 2 + len(text.encode("utf-16-le")) // 2,
                                "paragraph": {"elements": [{"textRun": {"content": text + "\n"}}]},
                            }
                        ]
                    }
                },
            }
        ],
    }


async def test_document_updates_use_revision_and_utf16_positions() -> None:
    state = document("Prior ")
    requests: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal state
        if request.method == "GET":
            assert request.url.params["includeTabsContent"] == "true"
            return httpx.Response(200, json=state)
        body = json.loads(request.content)
        assert body["writeControl"] == {"requiredRevisionId": "revision1"}
        requests.extend(body["requests"])
        assert body["requests"][0]["insertText"]["text"] == "Hello 🌍\nItem 1\nItem 2\n"
        assert body["requests"][0]["insertText"]["location"] == {"index": 7, "tabId": "tab1"}
        assert body["requests"][1]["updateParagraphStyle"]["range"]["endIndex"] == 16
        state = document("Prior Hello 🌍\nItem 1\nItem 2", "revision2")
        return httpx.Response(200, json={"writeControl": {"requiredRevisionId": "revision2"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = GoogleDocs(GoogleClient(token, client))
        args = {
            "document_id": "document1",
            "append_blocks": [
                {"type": "heading", "level": 1, "text": "Hello 🌍"},
                {"type": "bullet_list", "items": ["Item 1", "Item 2"]},
            ],
        }
        approved = await provider.snapshot("update_document", args)
        result = await provider.call("update_document", args | {"_snapshot": approved})
    assert result["verified"] and result["revision_id"] == "revision2"
    assert result["web_url"] == "https://docs.google.com/document/d/document1/edit"
    assert any("createParagraphBullets" in request for request in requests)


async def test_stale_document_approval_never_writes() -> None:
    state = document("Retained text")
    writes = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method != "GET":
            writes.append(request)
        return httpx.Response(200, json=state)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = GoogleDocs(GoogleClient(token, client))
        args = {
            "document_id": "document1",
            "replace_text": [{"find": "Retained", "replacement": "New"}],
        }
        approved = await provider.snapshot("update_document", args)
        state["revisionId"] = "collaborator-change"
        with pytest.raises(ConnectorError) as error:
            await provider.call("update_document", args | {"_snapshot": approved})
    assert error.value.code == "stale_action" and not writes


async def test_create_records_operation_and_reports_partial_resource() -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "GET" and request.url.host == "www.googleapis.com":
            return httpx.Response(200, json={"files": []})
        if request.method == "POST":
            assert json.loads(request.content)["appProperties"] == {
                "workspace_operation": "operation1"
            }
            return httpx.Response(200, json={"id": "created1"})
        return httpx.Response(403, json={"error": {"message": "PRIVATE_PROVIDER_BODY"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GoogleDocs(GoogleClient(token, client)).call(
            "create_document",
            {"title": "A real document", "blocks": [], "idempotency_key": "operation1"},
        )
    assert result["id"] == "created1"
    assert result["partial"] and not result["verified"]
    assert result["error_code"] == "PARTIAL_CREATION"
    assert "PRIVATE_PROVIDER_BODY" not in json.dumps(result)
    assert len([request for request in requests if request.method == "POST"]) == 1


async def test_reconcile_incomplete_create_does_not_duplicate_or_claim_success() -> None:
    writes = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method != "GET":
            writes.append(request)
        if request.url.host == "www.googleapis.com":
            assert "workspace_operation" in request.url.params["q"]
            return httpx.Response(200, json={"files": [{"id": "document1"}]})
        return httpx.Response(200, json=document("Incomplete"))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GoogleDocs(GoogleClient(token, client)).call(
            "create_document",
            {
                "title": "Report",
                "blocks": [{"type": "paragraph", "text": "Required complete content"}],
                "idempotency_key": "operation1",
            },
        )
    assert result["partial"] and not writes


async def test_create_populates_real_document_and_reads_back() -> None:
    current = document()
    created = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal current, created
        if request.url.host == "www.googleapis.com":
            assert request.method == "POST"
            assert json.loads(request.content)["mimeType"] == "application/vnd.google-apps.document"
            created = True
            return httpx.Response(200, json={"id": "document1"})
        if request.method == "GET":
            return httpx.Response(200, json=current)
        assert created
        body = json.loads(request.content)
        text = body["requests"][0]["insertText"]["text"]
        current = document(text, "revision2")
        return httpx.Response(200, json={"writeControl": {"requiredRevisionId": "revision2"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GoogleDocs(GoogleClient(token, client)).call(
            "create_document",
            {"title": "Report", "blocks": [{"type": "paragraph", "text": "Evidence-backed text"}]},
        )
    assert result["status"] == "created" and result["verified"]
    assert "Evidence-backed text" in result["text"]


def test_tabs_selection_and_payload_bounds() -> None:
    original = document()
    other = copy.deepcopy(original["tabs"][0])
    other["tabProperties"]["tabId"] = "tab2"
    original["tabs"].append(other)
    assert document_body(original, "tab2")[1] == "tab2"
    with pytest.raises(ConnectorError, match="tab"):
        document_body(original, "missing")
    with pytest.raises(ValidationError):
        CreateDocument(title="Report", blocks=[], requests=[{"deleteContentRange": {}}])
    with pytest.raises(ValidationError):
        UpdateDocument(document_id="document1")
    with pytest.raises(ValidationError):
        UpdateDocument(document_id="https://attacker.invalid/path", append_blocks=[])
    assert (
        text_requests([{"type": "paragraph", "text": "emoji 😀"}], 1, None)[0]["insertText"]["text"]
        == "emoji 😀\n"
    )


def test_native_tools_have_explicit_scope_alternatives_and_write_risk() -> None:
    definitions = tool_definitions()
    assert definitions["docs.get_document"].risk == "READ"
    for name in ["docs.create_document", "docs.update_document"]:
        assert definitions[name].risk == "ACCOUNT_WRITE"
        assert ("https://www.googleapis.com/auth/drive",) in definitions[name].scope_alternatives


@pytest.mark.parametrize(
    "find,provider_updates,expected_code",
    [
        ("Missing", True, "not_found"),
        ("Original", False, "readback_failed"),
        ("Original", True, None),
    ],
)
async def test_exact_replacement_requires_matching_text_and_verified_result(
    find: str, provider_updates: bool, expected_code: str | None
) -> None:
    state = document("Original content")
    writes = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal state
        if request.method == "GET":
            return httpx.Response(200, json=state)
        body = json.loads(request.content)
        writes.append(body)
        assert body["requests"][0]["replaceAllText"]["tabsCriteria"] == {"tabIds": ["tab1"]}
        if provider_updates:
            state = document("New content", "revision2")
        return httpx.Response(
            200, json={"writeControl": {"requiredRevisionId": state["revisionId"]}}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = GoogleDocs(GoogleClient(token, client))
        args = {"document_id": "document1", "replace_text": [{"find": find, "replacement": "New"}]}
        approved = await provider.snapshot("update_document", args)
        if expected_code:
            with pytest.raises(ConnectorError) as caught:
                await provider.call("update_document", args | {"_snapshot": approved})
            assert caught.value.code == expected_code
        else:
            assert (await provider.call("update_document", args | {"_snapshot": approved}))[
                "verified"
            ]
    assert len(writes) == (0 if find == "Missing" else 1)


async def test_native_tables_use_returned_cell_indices_in_reverse_order() -> None:
    state = document()
    cells: dict[int, dict[str, Any]] = {}
    populated = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal state
        if request.url.host == "www.googleapis.com":
            return httpx.Response(200, json={"id": "document1"})
        if request.method == "GET":
            return httpx.Response(200, json=state)
        body = json.loads(request.content)
        if "insertTable" in body["requests"][0]:
            assert body["requests"][0]["insertTable"] == {
                "rows": 2,
                "columns": 2,
                "endOfSegmentLocation": {"tabId": "tab1"},
            }
            rows = []
            for row in range(2):
                row_cells = []
                for column in range(2):
                    index = 5 + row * 4 + column * 2
                    paragraph = {
                        "startIndex": index,
                        "paragraph": {"elements": [{"textRun": {"content": "\n"}}]},
                    }
                    cells[index] = paragraph
                    row_cells.append({"content": [paragraph]})
                rows.append({"tableCells": row_cells})
            state["tabs"][0]["documentTab"]["body"]["content"] = [
                {"startIndex": 2, "endIndex": 14, "table": {"tableRows": rows}}
            ]
        else:
            for change in body["requests"]:
                insert = change["insertText"]
                populated.append(insert["location"]["index"])
                cells[insert["location"]["index"]]["paragraph"]["elements"][0]["textRun"][
                    "content"
                ] = insert["text"] + "\n"
        state["revisionId"] += "x"
        return httpx.Response(
            200, json={"writeControl": {"requiredRevisionId": state["revisionId"]}}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GoogleDocs(GoogleClient(token, client)).call(
            "create_document",
            {
                "title": "Table report",
                "blocks": [{"type": "table", "headers": ["A", "B"], "rows": [["One", "Two"]]}],
            },
        )
    assert result["verified"] and populated == [11, 9, 7, 5]
