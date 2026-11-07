from __future__ import annotations

import base64
import re
from email.message import EmailMessage
from email.policy import SMTP
from email.utils import getaddresses
from typing import Any

from mcp_workspace_common.errors import ConnectorError
from mcp_workspace_common.utils.artifacts import _artifact_bytes


def _draft_raw(args: dict[str, Any], reply: dict[str, Any] | None = None) -> str:
    message = EmailMessage(policy=SMTP)
    for name in ("to", "cc", "bcc"):
        values = args.get(name, [])
        values = [values] if isinstance(values, str) else values
        if values:
            joined = ", ".join(values)
            addresses = getaddresses(values)
            if (
                "\r" in joined
                or "\n" in joined
                or not addresses
                or any(
                    not re.fullmatch(r"[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+", addr)
                    for _, addr in addresses
                )
            ):
                raise ConnectorError("invalid_input", "Invalid email recipient")
            message[name.title()] = joined
    if not message.get("To"):
        raise ConnectorError("invalid_input", "A draft recipient is required")
    try:
        message["Subject"] = args.get("subject", "")
        if reply:
            original_id = reply.get("message_id_header")
            if original_id:
                message["In-Reply-To"] = original_id
                message["References"] = " ".join(
                    filter(None, [reply.get("references"), original_id])
                )
        message.set_content(args.get("body_text", ""))
        if args.get("body_html"):
            message.add_alternative(args["body_html"], subtype="html")
        for artifact in args.get("_attachments", []):
            data = _artifact_bytes(artifact)
            major, minor = artifact["mime_type"].split("/", 1)
            message.add_attachment(data, maintype=major, subtype=minor, filename=artifact["title"])
        return base64.urlsafe_b64encode(message.as_bytes()).decode()
    except (ValueError, TypeError, KeyError):
        raise ConnectorError("invalid_input", "Draft MIME could not be constructed") from None
