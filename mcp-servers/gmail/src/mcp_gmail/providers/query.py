from __future__ import annotations

import re
import shlex
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from mcp_workspace_common.constants import DEMO_NOW
from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.extraction import parse_gmail_message


def _gmail_match(message: dict[str, Any], query: str) -> bool:
    parsed = parse_gmail_message(message)
    try:
        terms = shlex.split(query)
    except ValueError:
        raise ConnectorError("invalid_query", "Unclosed quoted search phrase") from None
    if any(term in {"OR", "{", "}"} for term in terms):
        raise ConnectorError(
            "unsupported_query",
            "Mock search supports AND terms, phrases and common Gmail operators",
        )
    for term in terms:
        negate = term.startswith("-")
        term = term.lstrip("-") if negate else term
        key, sep, value = term.partition(":")
        value = value.lower()
        labels = [str(x).lower() for x in message.get("labelIds", [])]
        if not sep:
            matched = (
                term.lower()
                in " ".join(
                    [parsed["subject"], parsed["from"], parsed["to"], parsed["text"]]
                ).lower()
            )
        elif key in {"from", "to", "subject"}:
            matched = value in parsed[key].lower()
        elif key in {"label", "is", "in"}:
            aliases = {"read": "unread", "starred": "starred"}
            matched = aliases.get(value, value) in labels
            if value == "read":
                matched = not matched
        elif key == "has" and value == "attachment":
            matched = bool(parsed["attachments"])
        elif key in {"after", "before", "newer_than", "older_than"}:
            when = datetime.fromtimestamp(int(message["internalDate"]) / 1000, UTC)
            try:
                if key in {"newer_than", "older_than"}:
                    match = re.fullmatch(r"(\d+)([dmy])", value)
                    if not match:
                        raise ValueError
                    count, unit = match.groups()
                    target = DEMO_NOW - timedelta(
                        days=int(count) * {"d": 1, "m": 30, "y": 365}[unit]
                    )
                else:
                    target = datetime.fromisoformat(value.replace("/", "-")).replace(
                        tzinfo=ZoneInfo("America/Los_Angeles")
                    )
                matched = when > target if key in {"after", "newer_than"} else when < target
            except ValueError:
                raise ConnectorError("invalid_query", "Invalid Gmail date operator") from None
        else:
            raise ConnectorError("unsupported_query", "Unsupported mock Gmail search operator")
        if matched == negate:
            return False
    return True
