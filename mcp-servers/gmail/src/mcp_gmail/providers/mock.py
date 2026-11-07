from __future__ import annotations

import copy
import uuid
from typing import Any

from mcp_workspace_common.constants import DEMO_NOW
from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.extraction import parse_gmail_message
from mcp_workspace_common.mock.lookup import _find
from mcp_workspace_common.utils.results import _page, _source

from mcp_gmail.providers.mime import _draft_raw
from mcp_gmail.providers.query import _gmail_match


class MockGmail:
    _find = staticmethod(_find)

    def call(
        self, state: dict[str, Any], tool: str, args: dict[str, Any]
    ) -> tuple[dict[str, Any], bool]:
        if tool == "search_messages":
            messages = sorted(
                [x for x in state["messages"] if _gmail_match(x, args.get("query", ""))],
                key=lambda x: int(x["internalDate"]),
                reverse=True,
            )
            result = _page([parse_gmail_message(x) for x in messages], args, "messages")
            result["sources"] = [_source("gmail", m, True) for m in result["messages"]]
            return result, False
        if tool == "get_message":
            message = parse_gmail_message(self._find(state["messages"], args["message_id"]))
            return message | {"sources": [_source("gmail", message, True)]}, False
        if tool == "get_thread":
            messages = sorted(
                [x for x in state["messages"] if x["threadId"] == args["thread_id"]],
                key=lambda x: int(x["internalDate"]),
            )
            if not messages:
                raise ConnectorError("not_found", "Thread not found")
            limit = min(int(args.get("max_messages", 50)), 100)
            return {
                "id": args["thread_id"],
                "messages": [parse_gmail_message(x) for x in messages[:limit]],
                "truncated": len(messages) > limit,
                "sources": [
                    _source("gmail", parse_gmail_message(x), True) for x in messages[:limit]
                ],
            }, False
        if tool == "list_labels":
            return {"labels": state["labels"]}, False
        if tool == "create_draft":
            reply = (
                parse_gmail_message(self._find(state["messages"], args["reply_to_message_id"]))
                if args.get("reply_to_message_id")
                else None
            )
            raw = _draft_raw(args, reply)
            draft = {
                "id": f"draft-{uuid.uuid4().hex[:12]}",
                "raw": raw,
                "thread_id": reply["thread_id"] if reply else None,
                "message": parse_gmail_message({"raw": raw}),
                "status": "draft",
            }
            state["drafts"].append(draft)
            return {
                "id": draft["id"],
                "draft_id": draft["id"],
                "message": draft["message"],
                "status": "draft",
            }, True
        if tool == "send_draft":
            draft = self._find(state["drafts"], args["draft_id"])
            if args.get("_snapshot") != draft:
                raise ConnectorError(
                    "stale_action", "Draft changed or approved snapshot is missing"
                )
            sent = {
                "id": f"sent-{uuid.uuid4().hex[:12]}",
                "thread_id": draft["thread_id"],
                "raw": draft["raw"],
                "labelIds": ["SENT"],
                "status": "sent",
            }
            state["sent"].append(sent)
            state["drafts"].remove(draft)
            state["messages"].append(
                {
                    "id": sent["id"],
                    "threadId": sent["thread_id"] or sent["id"],
                    "raw": sent["raw"],
                    "labelIds": ["SENT"],
                    "internalDate": str(int(DEMO_NOW.timestamp() * 1000)),
                }
            )
            return {"id": sent["id"], "message_id": sent["id"], "status": "sent"}, True
        if tool == "apply_labels":
            messages = [self._find(state["messages"], mid) for mid in args["message_ids"]]
            for message in messages:
                message["labelIds"] = sorted(
                    (set(message["labelIds"]) | set(args.get("add", [])))
                    - set(args.get("remove", []))
                )
            return {"updated": len(messages)}, True
        raise ConnectorError("unknown_tool", "Unknown Gmail tool")

    def snapshot(self, state: dict[str, Any], tool: str, args: dict[str, Any]) -> dict[str, Any]:
        return (
            copy.deepcopy(self._find(state["drafts"], args["draft_id"]))
            if tool == "send_draft"
            else {}
        )
