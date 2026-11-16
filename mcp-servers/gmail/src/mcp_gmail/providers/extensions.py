from __future__ import annotations

from email.utils import getaddresses
from typing import Any

from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.extraction import (
    MAX_FILE_BYTES,
    ExtractionError,
    decode_base64url,
    extract_text,
    parse_gmail_message,
)
from mcp_workspace_common.providers.google_client import GoogleClient
from mcp_workspace_common.providers.identifiers import _identifier
from mcp_workspace_common.utils.results import _source

from mcp_gmail.providers.mime import _draft_raw

BASE = "https://gmail.googleapis.com/gmail/v1/users/me"
WRITE_MESSAGES = {"archive_message", "trash_message", "untrash_message"}


class GoogleGmailExtensions:
    def __init__(self, transport: GoogleClient) -> None:
        self._request = transport.request

    async def call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if tool == "get_draft":
            draft = await self._request(
                "GET",
                BASE + "/drafts/" + _identifier(args["draft_id"]),
                read=True,
                params={"format": "full"},
            )
            message = parse_gmail_message(draft.get("message", {}))
            return {
                "draft_id": draft.get("id"),
                "message": message,
                "sources": [_source("gmail", message)],
            }
        if tool == "get_attachment":
            return await self._attachment(args)
        if tool == "update_draft":
            snapshot = await self._approved(tool, args)
            reply = None
            if args.get("reply_to_message_id"):
                raw = await self._request(
                    "GET",
                    BASE + "/messages/" + _identifier(args["reply_to_message_id"]),
                    read=True,
                    params={"format": "full"},
                )
                reply = parse_gmail_message(raw)
            message = {"raw": _draft_raw(args, reply)}
            thread = reply.get("thread_id") if reply else snapshot.get("thread_id")
            if thread:
                message["threadId"] = thread
            result = await self._request(
                "PUT",
                BASE + "/drafts/" + _identifier(args["draft_id"]),
                json={"id": args["draft_id"], "message": message},
            )
            readback = await self.call("get_draft", args)
            self.verify_draft(args, readback["message"])
            return result | readback | {"status": "draft", "readback_verified": True}
        if tool in WRITE_MESSAGES:
            await self._approved(tool, args)
            url = BASE + "/messages/" + _identifier(args["message_id"])
            if tool == "archive_message":
                await self._request("POST", url + "/modify", json={"removeLabelIds": ["INBOX"]})
            else:
                await self._request(
                    "POST", url + ("/trash" if tool == "trash_message" else "/untrash"), json={}
                )
            readback = await self._request("GET", url, read=True, params={"format": "metadata"})
            labels = set(readback.get("labelIds", []))
            if (
                (tool == "archive_message" and "INBOX" in labels)
                or (tool == "trash_message" and "TRASH" not in labels)
                or (tool == "untrash_message" and "TRASH" in labels)
            ):
                raise ConnectorError(
                    "outcome_unknown",
                    "Mailbox change could not be verified; inspect the message before retrying",
                )
            return {
                "message_id": readback.get("id", args["message_id"]),
                "label_ids": sorted(labels),
                "status": tool.removesuffix("_message"),
                "readback_verified": True,
            }
        raise ConnectorError("unknown_tool", "Unknown Gmail tool")

    @staticmethod
    def verify_draft(args: dict[str, Any], current_message: dict[str, Any]) -> None:
        matched = current_message.get("subject", "") == args.get("subject", "")
        actual_body = (
            current_message.get("body_text", "")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .rstrip("\n")
        )
        expected_body = (
            args.get("body_text", "").replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
        )
        matched = matched and actual_body == expected_body
        for field in ("to", "cc", "bcc"):
            addresses = sorted(
                address.casefold()
                for _, address in getaddresses([current_message.get(field, "")])
                if address
            )
            matched = matched and addresses == sorted(
                address.casefold() for address in args.get(field, [])
            )
        attached = sorted(
            (item.get("filename"), item.get("mime_type"))
            for item in current_message.get("attachments", [])
        )
        expected = sorted(
            (item["title"], item["mime_type"]) for item in args.get("_attachments", [])
        )
        if not matched or attached != expected:
            raise ConnectorError(
                "outcome_unknown",
                "Draft readback differs from the approved content; inspect the draft before retrying",
            )

    async def snapshot(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if tool == "update_draft":
            draft = await self._request(
                "GET",
                BASE + "/drafts/" + _identifier(args["draft_id"]),
                read=True,
                params={"format": "raw"},
            )
            message = draft.get("message", {})
            return {
                "id": draft.get("id"),
                "raw": message.get("raw"),
                "thread_id": message.get("threadId"),
                "message": parse_gmail_message(message),
            }
        if tool in WRITE_MESSAGES:
            message = await self._request(
                "GET",
                BASE + "/messages/" + _identifier(args["message_id"]),
                read=True,
                params={"format": "metadata"},
            )
            return {
                "id": message.get("id"),
                "history_id": message.get("historyId"),
                "label_ids": sorted(message.get("labelIds", [])),
                "message": parse_gmail_message(message),
            }
        return {}

    async def _approved(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        approved = args.get("_snapshot")
        if not approved:
            raise ConnectorError("stale_action", "Approved message snapshot is required")
        if await self.snapshot(tool, args) != approved:
            raise ConnectorError("stale_action", "Message changed after approval")
        return dict(approved)

    async def _attachment(self, args: dict[str, Any]) -> dict[str, Any]:
        message_id = _identifier(args["message_id"])
        attachment_id = _identifier(args["attachment_id"])
        message = await self._request(
            "GET", BASE + "/messages/" + message_id, read=True, params={"format": "full"}
        )
        queue = [message.get("payload", {})]
        attachment = None
        for _ in range(1000):
            if not queue:
                break
            part = queue.pop()
            if part.get("body", {}).get("attachmentId") == attachment_id:
                attachment = part
                break
            queue.extend(part.get("parts", []))
        if not attachment:
            raise ConnectorError("not_found", "Attachment not found in the selected message")
        if int(attachment.get("body", {}).get("size", 0)) > MAX_FILE_BYTES:
            raise ConnectorError("file_too_large", "Attachment exceeds the extraction limit")
        result = await self._request(
            "GET", BASE + "/messages/" + message_id + "/attachments/" + attachment_id, read=True
        )
        try:
            data = decode_base64url(result.get("data", ""))
            if len(data) > MAX_FILE_BYTES:
                raise ConnectorError("file_too_large", "Attachment exceeds the extraction limit")
            extracted = extract_text(
                data,
                attachment.get("mimeType", "application/octet-stream"),
                min(int(args.get("max_chars", 20000)), 100000),
            )
        except (ValueError, ExtractionError):
            raise ConnectorError(
                "extraction_failed", "Attachment content could not be extracted safely"
            ) from None
        parsed = parse_gmail_message(message)
        return extracted | {
            "message_id": message_id,
            "attachment_id": attachment_id,
            "filename": attachment.get("filename", ""),
            "mime_type": attachment.get("mimeType"),
            "size": len(data),
            "sources": [_source("gmail", parsed)],
        }
