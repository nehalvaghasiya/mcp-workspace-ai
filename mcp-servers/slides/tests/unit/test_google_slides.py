from __future__ import annotations

import copy
import json
import re
from typing import Any

import httpx
import pytest
from mcp_slides.providers.google import GoogleSlides
from mcp_slides.schemas.create_presentation import CreatePresentation
from mcp_slides.schemas.update_presentation import UpdatePresentation
from mcp_slides.server import tool_definitions
from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.providers.google_client import GoogleClient
from pydantic import ValidationError


async def token() -> str:
    return "synthetic-token"


class PresentationHTTP:
    def __init__(self) -> None:
        self.state: dict[str, Any] = {
            "presentationId": "presentation1",
            "title": "Actual deck",
            "revisionId": "revision1",
            "slides": [],
        }
        self.writes: list[dict[str, Any]] = []
        self.created_metadata: dict[str, Any] | None = None
        self.objects: dict[str, dict[str, Any]] = {}
        self.version = 1
        self.ignore_replacements = False

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.host == "www.googleapis.com":
            if request.method == "GET":
                return httpx.Response(200, json={"files": []})
            self.created_metadata = json.loads(request.content)
            self.state["title"] = self.created_metadata["name"]
            return httpx.Response(200, json={"id": "presentation1"})
        if request.method == "GET":
            return httpx.Response(200, json=copy.deepcopy(self.state))
        body = json.loads(request.content)
        assert body["writeControl"]["requiredRevisionId"] == self.state["revisionId"]
        self.writes.append(body)
        for change in body["requests"]:
            if "replaceAllText" in change and not self.ignore_replacements:
                replacement = change["replaceAllText"]
                selected = replacement.get("pageObjectIds", [])
                pattern = re.compile(
                    re.escape(replacement["containsText"]["text"]),
                    0 if replacement["containsText"]["matchCase"] else re.IGNORECASE,
                )
                for slide in self.state["slides"]:
                    if selected and slide["objectId"] not in selected:
                        continue
                    for element in slide["pageElements"]:
                        for run in element.get("shape", {}).get("text", {}).get("textElements", []):
                            if "textRun" in run:
                                run["textRun"]["content"] = pattern.sub(
                                    lambda _, value=replacement["replaceText"]: value,
                                    run["textRun"]["content"],
                                )
            if "createSlide" in change:
                identifier = change["createSlide"]["objectId"]
                notes = {"objectId": identifier + "_notes", "shape": {"text": {"textElements": []}}}
                self.objects[notes["objectId"]] = notes
                slide = {
                    "objectId": identifier,
                    "pageElements": [],
                    "slideProperties": {
                        "notesPage": {
                            "notesProperties": {"speakerNotesObjectId": notes["objectId"]},
                            "pageElements": [notes],
                        }
                    },
                }
                self.state["slides"].append(slide)
            if "createShape" in change:
                props = change["createShape"]
                shape = {"objectId": props["objectId"], "shape": {"text": {"textElements": []}}}
                self.objects[props["objectId"]] = shape
                next(
                    slide
                    for slide in self.state["slides"]
                    if slide["objectId"] == props["elementProperties"]["pageObjectId"]
                )["pageElements"].append(shape)
            if "createTable" in change:
                props = change["createTable"]
                table = {
                    "objectId": props["objectId"],
                    "table": {
                        "tableRows": [
                            {
                                "tableCells": [
                                    {"text": {"textElements": []}} for _ in range(props["columns"])
                                ]
                            }
                            for _ in range(props["rows"])
                        ]
                    },
                }
                self.objects[props["objectId"]] = table
                next(
                    slide
                    for slide in self.state["slides"]
                    if slide["objectId"] == props["elementProperties"]["pageObjectId"]
                )["pageElements"].append(table)
            if "insertText" in change:
                props = change["insertText"]
                target = self.objects[props["objectId"]]
                if "cellLocation" in props:
                    cell = props["cellLocation"]
                    elements = target["table"]["tableRows"][cell["rowIndex"]]["tableCells"][
                        cell["columnIndex"]
                    ]["text"]["textElements"]
                else:
                    elements = target["shape"]["text"]["textElements"]
                elements.append({"textRun": {"content": props["text"]}})
            if "deleteText" in change:
                self.objects[change["deleteText"]["objectId"]]["shape"]["text"]["textElements"] = []
            if "deleteObject" in change:
                self.state["slides"] = [
                    slide
                    for slide in self.state["slides"]
                    if slide["objectId"] != change["deleteObject"]["objectId"]
                ]
        self.version += 1
        self.state["revisionId"] = f"revision{self.version}"
        return httpx.Response(
            200, json={"writeControl": {"requiredRevisionId": self.state["revisionId"]}}
        )


async def test_create_deck_has_real_shapes_tables_notes_and_operation_marker() -> None:
    transport = PresentationHTTP()
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = GoogleSlides(GoogleClient(token, client))
        result = await provider.call(
            "create_presentation",
            {
                "title": "Generated deck",
                "idempotency_key": "operation1",
                "slides": [
                    {
                        "title": "A real slide",
                        "body": "Source-backed summary",
                        "bullets": ["First decision", "Second decision"],
                        "tables": [
                            {
                                "type": "table",
                                "headers": ["Owner", "Status"],
                                "rows": [["Alex", "Ready"]],
                            }
                        ],
                        "notes": "Explain the decision",
                    }
                ],
            },
        )
    assert result["status"] == "created" and result["verified"]
    assert result["web_url"] == "https://docs.google.com/presentation/d/presentation1/edit"
    assert transport.created_metadata["appProperties"] == {"workspace_operation": "operation1"}
    assert "Source-backed summary\nFirst decision\nSecond decision" in result["text"]
    assert "Explain the decision" in result["text"]
    assert len(result["presentation"]["slides"]) == 1
    assert any("createTable" in change for change in transport.writes[0]["requests"])
    assert transport.writes[1]["requests"][0]["insertText"]["text"] == "Explain the decision"


async def test_shape_edit_and_appended_slide_enforce_approved_revision() -> None:
    transport = PresentationHTTP()
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = GoogleSlides(GoogleClient(token, client))
        created = await provider.call(
            "create_presentation",
            {"title": "Deck", "slides": [{"title": "Original", "body": "Retained"}]},
        )
        slide = created["presentation"]["slides"][0]
        shape_id = slide["pageElements"][0]["objectId"]
        args = {
            "presentation_id": "presentation1",
            "shape_text": [{"object_id": shape_id, "text": "Updated title"}],
            "append_slides": [{"title": "New slide", "body": "New details"}],
        }
        snapshot = await provider.snapshot("update_presentation", args)
        result = await provider.call("update_presentation", args | {"_snapshot": snapshot})
    assert result["status"] == "updated"
    assert "Updated title" in result["text"] and "New details" in result["text"]
    assert len(result["presentation"]["slides"]) == 2
    assert transport.writes[-1]["writeControl"]["requiredRevisionId"] == snapshot["revision_id"]


async def test_stale_approval_and_unknown_shapes_never_write() -> None:
    transport = PresentationHTTP()
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = GoogleSlides(GoogleClient(token, client))
        args = {"presentation_id": "presentation1", "append_slides": [{"title": "New"}]}
        snapshot = await provider.snapshot("update_presentation", args)
        transport.state["revisionId"] = "changed-by-collaborator"
        with pytest.raises(ConnectorError) as error:
            await provider.call("update_presentation", args | {"_snapshot": snapshot})
        assert error.value.code == "stale_action"
        args = {
            "presentation_id": "presentation1",
            "shape_text": [{"object_id": "missing_shape", "text": "Change"}],
        }
        snapshot = await provider.snapshot("update_presentation", args)
        with pytest.raises(ConnectorError) as error:
            await provider.call("update_presentation", args | {"_snapshot": snapshot})
        assert error.value.code == "not_found"
    assert not transport.writes


async def test_selected_slide_deletion_preserves_other_slides() -> None:
    transport = PresentationHTTP()
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = GoogleSlides(GoogleClient(token, client))
        created = await provider.call(
            "create_presentation",
            {"title": "Deck", "slides": [{"title": "Keep"}, {"title": "Remove"}]},
        )
        slides = created["presentation"]["slides"]
        args = {"presentation_id": "presentation1", "delete_slide_ids": [slides[1]["objectId"]]}
        snapshot = await provider.snapshot("update_presentation", args)
        result = await provider.call("update_presentation", args | {"_snapshot": snapshot})
    assert len(result["presentation"]["slides"]) == 1
    assert result["presentation"]["slides"][0]["objectId"] == slides[0]["objectId"]


async def test_create_returns_partial_when_google_file_exists_but_content_failed() -> None:
    writes = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "www.googleapis.com":
            writes.append(request)
            return httpx.Response(200, json={"id": "created1"})
        return httpx.Response(403, json={"error": {"message": "PRIVATE_PROVIDER_BODY"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GoogleSlides(GoogleClient(token, client)).call(
            "create_presentation", {"title": "Deck", "slides": [{"title": "Required title"}]}
        )
    assert result["id"] == "created1" and result["partial"] and not result["verified"]
    assert "PRIVATE_PROVIDER_BODY" not in json.dumps(result)
    assert len(writes) == 1


async def test_reconcile_does_not_claim_incomplete_presentation_succeeded() -> None:
    writes = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method != "GET":
            writes.append(request)
        if request.url.host == "www.googleapis.com":
            return httpx.Response(200, json={"files": [{"id": "presentation1"}]})
        return httpx.Response(
            200,
            json={
                "presentationId": "presentation1",
                "title": "Incomplete",
                "revisionId": "revision1",
                "slides": [],
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await GoogleSlides(GoogleClient(token, client)).call(
            "create_presentation",
            {
                "title": "Deck",
                "slides": [{"title": "Required title"}],
                "idempotency_key": "operation1",
            },
        )
    assert result["partial"] and not result["verified"] and not writes


def test_typed_schema_rejects_raw_requests_and_invalid_targets() -> None:
    with pytest.raises(ValidationError):
        UpdatePresentation(presentation_id="presentation1")
    with pytest.raises(ValidationError):
        UpdatePresentation(
            presentation_id="presentation1",
            shape_text=[{"object_id": "https://attacker.invalid", "text": "Text"}],
        )
    with pytest.raises(ValidationError):
        CreatePresentation(
            title="Deck", slides=[{"title": "Title"}], requests=[{"deleteObject": {}}]
        )
    definitions = tool_definitions()
    assert definitions["slides.get_presentation"].risk == "READ"
    assert definitions["slides.create_presentation"].risk == "ACCOUNT_WRITE"
    assert definitions["slides.update_presentation"].risk == "DESTRUCTIVE"


@pytest.mark.parametrize(
    "find,ignore,expected_code",
    [
        ("Missing", False, "not_found"),
        ("Original", True, "readback_failed"),
        ("Original", False, None),
    ],
)
async def test_replacement_only_updates_are_verified(
    find: str, ignore: bool, expected_code: str | None
) -> None:
    transport = PresentationHTTP()
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = GoogleSlides(GoogleClient(token, client))
        await provider.call(
            "create_presentation", {"title": "Deck", "slides": [{"title": "Original title"}]}
        )
        before = len(transport.writes)
        transport.ignore_replacements = ignore
        args = {
            "presentation_id": "presentation1",
            "replace_text": [{"find": find, "replacement": "Revised"}],
        }
        snapshot = await provider.snapshot("update_presentation", args)
        if expected_code:
            with pytest.raises(ConnectorError) as caught:
                await provider.call("update_presentation", args | {"_snapshot": snapshot})
            assert caught.value.code == expected_code
        else:
            assert (await provider.call("update_presentation", args | {"_snapshot": snapshot}))[
                "verified"
            ]
    assert len(transport.writes) - before == (0 if find == "Missing" else 1)
