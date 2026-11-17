from __future__ import annotations

import asyncio
from typing import Any

from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.extraction import parse_gmail_message
from mcp_workspace_common.providers.google_client import GoogleClient
from mcp_workspace_common.providers.identifiers import _identifier
from mcp_workspace_common.utils.results import _source

from mcp_gmail.providers.extensions import WRITE_MESSAGES, GoogleGmailExtensions
from mcp_gmail.providers.mime import _draft_raw


class GoogleGmail:
    def __init__(self, transport: GoogleClient) -> None:
        self._request = transport.request
        self.extensions = GoogleGmailExtensions(transport)

    async def call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        base = "https://gmail.googleapis.com/gmail/v1/users/me"
        if tool == "get_messages":
            identifiers = list(dict.fromkeys(args["message_ids"]))
            if not 1 <= len(identifiers) <= 20:
                raise ConnectorError("invalid_input", "Select between 1 and 20 messages")
            semaphore = asyncio.Semaphore(4)

            async def read_selected(message_id: str) -> dict[str, Any]:
                async with semaphore:
                    try:
                        return await self.call(
                            "get_message",
                            {"message_id": message_id, "format": args.get("format", "full")},
                        )
                    except ConnectorError as exc:
                        return {"unavailable_id": message_id, "code": exc.code}

            rows = await asyncio.gather(*(read_selected(message_id) for message_id in identifiers))
            messages = [row for row in rows if "unavailable_id" not in row]
            unavailable = [row for row in rows if "unavailable_id" in row]
            return {
                "messages": messages,
                "unavailable": unavailable,
                "partial": bool(unavailable),
                "sources": [
                    source for message in messages for source in message.get("sources", [])
                ],
            }
        if tool in {"get_draft", "get_attachment", "update_draft", *WRITE_MESSAGES}:
            return await self.extensions.call(tool, args)
        if tool == "search_messages":
            result = await self._request(
                "GET",
                base + "/messages",
                read=True,
                params={
                    "q": args.get("query", ""),
                    "maxResults": min(int(args.get("max_results", 20)), 100),
                    **({"pageToken": args["page_token"]} if args.get("page_token") else {}),
                },
            )
            semaphore = asyncio.Semaphore(5)

            async def fetch(item: dict[str, Any]) -> dict[str, Any]:
                async with semaphore:
                    raw = await self._request(
                        "GET",
                        base + "/messages/" + _identifier(item["id"]),
                        read=True,
                        params={
                            "format": "metadata",
                            "metadataHeaders": ["Subject", "From", "To", "Date"],
                        },
                    )
                    return parse_gmail_message(raw) | {"snippet": raw.get("snippet", "")}

            messages = await asyncio.gather(
                *(fetch(item) for item in result.get("messages", [])[:100])
            )
            return {
                "messages": messages,
                "next_page_token": result.get("nextPageToken"),
                "sources": [_source("gmail", x) for x in messages],
            }
        if tool == "get_message":
            raw = await self._request(
                "GET",
                base + "/messages/" + _identifier(args["message_id"]),
                read=True,
                params={
                    "format": "full" if args.get("format") == "text" else args.get("format", "full")
                },
            )
            message = parse_gmail_message(raw)
            return message | {"sources": [_source("gmail", message)]}
        if tool == "get_thread":
            raw = await self._request(
                "GET",
                base + "/threads/" + _identifier(args["thread_id"]),
                read=True,
                params={"format": "full"},
            )
            messages = sorted(raw.get("messages", []), key=lambda x: int(x.get("internalDate", 0)))
            limit = min(int(args.get("max_messages", 50)), 100)
            parsed = [parse_gmail_message(x) for x in messages[:limit]]
            return {
                "id": raw.get("id"),
                "messages": parsed,
                "truncated": len(messages) > limit,
                "sources": [_source("gmail", x) for x in parsed],
            }
        if tool == "list_labels":
            return await self._request("GET", base + "/labels", read=True)
        if tool == "create_draft":
            reply = (
                await self.call("get_message", {"message_id": args["reply_to_message_id"]})
                if args.get("reply_to_message_id")
                else None
            )
            raw = _draft_raw(args, reply)
            message = {"raw": raw} | ({"threadId": reply["thread_id"]} if reply else {})
            result = await self._request("POST", base + "/drafts", json={"message": message})
            if args.get("idempotency_key"):
                if not result.get("id"):
                    raise ConnectorError(
                        "outcome_unknown",
                        "Draft creation returned no ID; inspect Drafts before retrying",
                    )
                readback = await self.extensions.call("get_draft", {"draft_id": result["id"]})
                self.extensions.verify_draft(args, readback["message"])
                result.update(readback | {"readback_verified": True})
            return result | {"draft_id": result.get("id"), "status": "draft"}
        if tool == "send_draft":
            approved = args.get("_snapshot")
            if not approved or not approved.get("raw") or approved.get("id") != args["draft_id"]:
                raise ConnectorError("stale_action", "Approved full MIME snapshot is required")
            current = await self.snapshot(tool, args)
            if current != approved:
                raise ConnectorError("stale_action", "Draft changed after approval")
            # Full approved MIME is supplied atomically: Google's send method can
            # replace the existing draft message as part of the same send call.
            message = {"raw": approved["raw"]}
            if approved.get("thread_id"):
                message["threadId"] = approved["thread_id"]
            result = await self._request(
                "POST", base + "/drafts/send", json={"id": args["draft_id"], "message": message}
            )
            return result | {"message_id": result.get("id"), "status": "sent"}
        if tool == "apply_labels":
            await self._request(
                "POST",
                base + "/messages/batchModify",
                json={
                    "ids": args["message_ids"],
                    "addLabelIds": args.get("add", []),
                    "removeLabelIds": args.get("remove", []),
                },
            )
            if args.get("idempotency_key"):
                for message_id in args["message_ids"]:
                    message = await self._request(
                        "GET",
                        base + "/messages/" + _identifier(message_id),
                        read=True,
                        params={"format": "metadata"},
                    )
                    labels = set(message.get("labelIds", []))
                    if (
                        not set(args.get("add", [])) <= labels
                        or set(args.get("remove", [])) & labels
                    ):
                        raise ConnectorError(
                            "outcome_unknown",
                            "Label changes could not be verified; inspect messages before retrying",
                        )
            return {"updated": len(args["message_ids"])}
        raise ConnectorError("unknown_tool", "Unknown Gmail tool")

    async def snapshot(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if tool == "update_draft" or tool in WRITE_MESSAGES:
            return await self.extensions.snapshot(tool, args)
        if tool != "send_draft":
            return {}
        draft = await self._request(
            "GET",
            f"https://gmail.googleapis.com/gmail/v1/users/me/drafts/{_identifier(args['draft_id'])}",
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
