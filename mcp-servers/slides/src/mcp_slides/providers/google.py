from __future__ import annotations

import hashlib
from typing import Any
from uuid import uuid4

from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.providers.google_client import GoogleClient
from mcp_workspace_common.providers.identifiers import _identifier
from pydantic import BaseModel

from mcp_slides.providers.content import presentation_text, slide_requests
from mcp_slides.providers.create import create_presentation
from mcp_slides.providers.verification import expected_edits, matches_presentation, verify_edits
from mcp_slides.schemas.create_presentation import CreatePresentation
from mcp_slides.schemas.presentation_id import PresentationId
from mcp_slides.schemas.update_presentation import UpdatePresentation

BASE = "https://slides.googleapis.com/v1/presentations/"
DRIVE = "https://www.googleapis.com/drive/v3/files"


class GoogleSlides:
    def __init__(self, transport: GoogleClient) -> None:
        self._request = transport.request

    async def _get(self, identifier: str) -> dict[str, Any]:
        return dict(await self._request("GET", BASE + _identifier(identifier), read=True))

    def _result(self, presentation: dict[str, Any]) -> dict[str, Any]:
        identifier = presentation.get("presentationId", presentation.get("id", ""))
        title = presentation.get("title", presentation.get("name", identifier))
        url = f"https://docs.google.com/presentation/d/{identifier}/edit"
        return {
            "id": identifier,
            "title": title,
            "mime_type": "application/vnd.google-apps.presentation",
            "web_url": url,
            "revision_id": presentation.get("revisionId"),
            "presentation": presentation,
            "text": presentation_text(presentation),
            "sources": [
                {"provider": "slides", "resource_id": identifier, "title": title, "url": url}
            ],
            "verified": True,
        }

    async def snapshot(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if tool == "create_presentation":
            if not args.get("parent_id"):
                return {}
            return dict(
                await self._request(
                    "GET",
                    DRIVE + "/" + _identifier(args["parent_id"]),
                    read=True,
                    params={
                        "fields": "id,name,mimeType,version,capabilities(canAddChildren)",
                        "supportsAllDrives": "true",
                    },
                )
            )
        if tool != "update_presentation":
            return {}
        presentation = await self._get(args["presentation_id"])
        if not presentation.get("revisionId"):
            raise ConnectorError(
                "permission_denied", "An editable presentation revision is required"
            )
        return {
            "presentation_id": args["presentation_id"],
            "title": presentation.get("title", ""),
            "revision_id": presentation["revisionId"],
        }

    async def _batch(
        self, identifier: str, presentation: dict[str, Any], requests: list[dict[str, Any]]
    ) -> dict[str, Any]:
        if not presentation.get("revisionId"):
            raise ConnectorError(
                "permission_denied", "An editable presentation revision is required"
            )
        reply = await self._request(
            "POST",
            BASE + identifier + ":batchUpdate",
            json={
                "requests": requests,
                "writeControl": {"requiredRevisionId": presentation["revisionId"]},
            },
        )
        refreshed = await self._get(identifier)
        written = reply.get("writeControl", {}).get("requiredRevisionId")
        if written and written != refreshed.get("revisionId"):
            raise ConnectorError(
                "stale_action", "Presentation changed while applying approved edits"
            )
        return refreshed

    async def _notes(
        self, identifier: str, presentation: dict[str, Any], notes: dict[str, str]
    ) -> dict[str, Any]:
        if not set(notes) <= {slide["objectId"] for slide in presentation.get("slides", [])}:
            raise ConnectorError("readback_failed", "Created slides could not be read back")
        requests = []
        for slide in presentation.get("slides", []):
            if slide["objectId"] not in notes:
                continue
            object_id = (
                slide.get("slideProperties", {})
                .get("notesPage", {})
                .get("notesProperties", {})
                .get("speakerNotesObjectId")
            )
            if not object_id:
                raise ConnectorError("readback_failed", "Speaker notes target is unavailable")
            requests.append(
                {
                    "insertText": {
                        "objectId": object_id,
                        "text": notes[slide["objectId"]],
                        "insertionIndex": 0,
                    }
                }
            )
        return await self._batch(identifier, presentation, requests) if requests else presentation

    async def call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        models: dict[str, type[BaseModel]] = {
            "get_presentation": PresentationId,
            "create_presentation": CreatePresentation,
            "update_presentation": UpdatePresentation,
        }
        if tool not in models:
            raise ConnectorError("unknown_tool", "Unknown Google Slides tool")
        clean = (
            models[tool]
            .model_validate(
                {
                    key: value
                    for key, value in args.items()
                    if not key.startswith("_") and key != "idempotency_key"
                }
            )
            .model_dump(mode="json")
        )
        args = clean | {
            key: value
            for key, value in args.items()
            if key.startswith("_") or key == "idempotency_key"
        }
        if tool == "create_presentation":
            return await create_presentation(self, args)
        identifier = args["presentation_id"]
        presentation = await self._get(identifier)
        if tool == "get_presentation":
            return self._result(presentation)
        approved = args.get("_snapshot")
        if (
            not approved
            or approved != await self.snapshot(tool, args)
            or approved["revision_id"] != presentation.get("revisionId")
        ):
            raise ConnectorError(
                "stale_action", "Presentation changed or approved revision is missing"
            )
        slide_ids = {slide["objectId"] for slide in presentation.get("slides", [])}
        shapes = {
            element["objectId"]
            for slide in presentation.get("slides", [])
            for element in slide.get("pageElements", [])
            if "shape" in element
        }
        requests = []
        for replacement in args["replace_text"]:
            targets = replacement["slide_ids"]
            if not set(targets) <= slide_ids:
                raise ConnectorError("not_found", "A selected presentation slide is unavailable")
            change = {
                "containsText": {
                    "text": replacement["find"],
                    "matchCase": replacement["match_case"],
                },
                "replaceText": replacement["replacement"],
            }
            if targets:
                change["pageObjectIds"] = targets
            requests.append({"replaceAllText": change})
        for change in args["shape_text"]:
            if change["object_id"] not in shapes:
                raise ConnectorError("not_found", "The selected text shape is unavailable")
            requests.append(
                {"deleteText": {"objectId": change["object_id"], "textRange": {"type": "ALL"}}}
            )
            if change["text"]:
                requests.append(
                    {
                        "insertText": {
                            "objectId": change["object_id"],
                            "text": change["text"],
                            "insertionIndex": 0,
                        }
                    }
                )
        if not set(args["delete_slide_ids"]) <= slide_ids:
            raise ConnectorError("not_found", "A selected presentation slide is unavailable")
        expected = expected_edits(presentation, args)
        requests.extend(
            {"deleteObject": {"objectId": identifier}} for identifier in args["delete_slide_ids"]
        )
        prefix = (
            "ws_"
            + hashlib.sha256(str(args.get("idempotency_key") or uuid4().hex).encode()).hexdigest()[
                :16
            ]
        )
        appended, notes = slide_requests(args["append_slides"], prefix)
        presentation = await self._batch(identifier, presentation, [*requests, *appended])
        presentation = await self._notes(identifier, presentation, notes)
        if not verify_edits(presentation, expected, args["delete_slide_ids"]):
            raise ConnectorError(
                "readback_failed",
                "Approved presentation changes could not be verified; inspect before retrying",
            )
        if not matches_presentation(presentation, args["append_slides"]):
            raise ConnectorError(
                "readback_failed",
                "Approved presentation content could not be verified; inspect before retrying",
            )
        return self._result(presentation) | {
            "status": "updated",
            "operation_id": args.get("idempotency_key"),
        }
