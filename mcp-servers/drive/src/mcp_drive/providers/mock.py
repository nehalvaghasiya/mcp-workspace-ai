from __future__ import annotations

import base64
import uuid
from typing import Any

from mcp_workspace_common.constants import DEMO_NOW, EXPORTS, FOLDER
from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.extraction import ExtractionError, decode_base64url, extract_text
from mcp_workspace_common.mock.lookup import _find
from mcp_workspace_common.utils.artifacts import _artifact_bytes
from mcp_workspace_common.utils.results import _page, _source

from mcp_drive.providers.query import _drive_match


class MockDrive:
    _find = staticmethod(_find)

    def _file(self, state: dict[str, Any], file_id: str) -> dict[str, Any]:
        item = self._find(state["files"], file_id)
        if not item.get("selected", True) or not item.get("accessible", True):
            raise ConnectorError(
                "permission_denied", "File is unavailable to this app; open or select it first"
            )
        return item

    def call(
        self, state: dict[str, Any], tool: str, args: dict[str, Any]
    ) -> tuple[dict[str, Any], bool]:
        if tool in {"search_files", "list_folder"}:
            parent = args.get("folder_id") if tool == "list_folder" else args.get("parent_id")
            if parent and parent != "root":
                folder = self._file(state, parent)
                if folder["mimeType"] != FOLDER:
                    raise ConnectorError("invalid_input", "Target is not a folder")
            query = str(args.get("query", ""))
            files = [
                x
                for x in state["files"]
                if x.get("selected", True)
                and x.get("accessible", True)
                and not x.get("trashed")
                and (not parent or parent in x.get("parents", []))
                and (not args.get("mime_types") or x["mimeType"] in args["mime_types"])
            ]
            if query:
                files = [x for x in files if _drive_match(x, query)]
            result = _page(
                [
                    {k: v for k, v in x.items() if k not in {"content", "content_base64"}}
                    for x in files
                ],
                args,
                "files",
            )
            result["scope_note"] = (
                "Synthetic app-created/selected files only; drive.file is not whole-Drive access"
            )
            result["sources"] = [_source("drive", x, True) for x in result["files"]]
            return result, False
        if tool in {"get_file_metadata", "read_file"}:
            item = self._file(state, args["file_id"])
            metadata = {k: v for k, v in item.items() if k not in {"content", "content_base64"}}
            if tool == "get_file_metadata":
                return metadata | {"sources": [_source("drive", item, True)]}, False
            mime = item["mimeType"]
            max_chars = int(args.get("max_chars", 20000))
            if mime in EXPORTS:
                mime = "text/plain"  # Fixtures contain clearly labeled synthetic exports.
            if item.get("content_base64"):
                data = decode_base64url(item["content_base64"])
            else:
                data = item.get("content", "").encode()
            try:
                result = extract_text(data, mime, max_chars)
            except ExtractionError as exc:
                raise ConnectorError("extraction_failed", str(exc)) from None
            return result | {
                "id": item["id"],
                "name": item["name"],
                "sources": [_source("drive", item, True)],
            }, False
        if tool in {"create_folder", "upload_artifact"}:
            parent = args.get("parent_id") or args.get("folder_id") or "root"
            if parent != "root":
                folder = self._file(state, parent)
                if folder["mimeType"] != FOLDER:
                    raise ConnectorError("invalid_input", "Target is not a folder")
                if args.get("_snapshot") is not None and args["_snapshot"] != folder:
                    raise ConnectorError("stale_action", "Destination folder changed")
            if tool == "create_folder":
                item = {
                    "id": f"folder-{uuid.uuid4().hex[:12]}",
                    "name": args["name"],
                    "mimeType": FOLDER,
                    "parents": [parent],
                    "selected": True,
                }
            else:
                artifact = args.get("_artifact")
                if not artifact:
                    raise ConnectorError(
                        "artifact_unavailable", "A verified owned artifact is required"
                    )
                data = _artifact_bytes(artifact)
                item = {
                    "id": f"file-{uuid.uuid4().hex[:12]}",
                    "name": args.get("target_name") or artifact["title"],
                    "mimeType": artifact["mime_type"],
                    "parents": [parent],
                    "content_base64": base64.urlsafe_b64encode(data).decode(),
                    "sha256": artifact["sha256"],
                    "selected": True,
                }
            item.update(
                {
                    "version": "1",
                    "modifiedTime": DEMO_NOW.isoformat(),
                    "capabilities": {"canDownload": True},
                }
            )
            state["files"].append(item)
            return {k: v for k, v in item.items() if k != "content_base64"}, True
        raise ConnectorError("unknown_tool", "Unknown Drive tool")

    def snapshot(self, state: dict[str, Any], tool: str, args: dict[str, Any]) -> dict[str, Any]:
        return self._file(state, args["folder_id"]) if args.get("folder_id") else {}
