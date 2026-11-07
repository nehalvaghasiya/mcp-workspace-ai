from __future__ import annotations

import base64
import binascii
from email import policy
from email.parser import BytesParser
from typing import Any

from mcp_workspace_common.errors import ExtractionError
from mcp_workspace_common.extraction.constants import (
    MAX_FILE_BYTES,
)

from .html_text import html_to_text


def decode_base64url(value: str) -> bytes:
    if len(value) > MAX_FILE_BYTES * 2:
        raise ExtractionError("MIME body exceeds extraction limit")
    try:
        return base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    except (ValueError, binascii.Error):
        raise ExtractionError("Invalid MIME body encoding") from None


def parse_gmail_message(message: dict[str, Any], max_chars: int = 20000) -> dict[str, Any]:
    """Normalize Gmail's multipart resource or raw MIME without returning active HTML."""
    headers: dict[str, str] = {}
    text_parts: list[str] = []
    html_parts: list[str] = []
    attachments: list[dict[str, Any]] = []
    if message.get("raw"):
        parsed = BytesParser(policy=policy.default).parsebytes(decode_base64url(message["raw"]))
        headers = {
            key.lower(): str(parsed.get(key, ""))
            for key in [
                "Subject",
                "From",
                "To",
                "Cc",
                "Bcc",
                "Date",
                "Message-ID",
                "In-Reply-To",
                "References",
            ]
        }
        for part in list(parsed.walk())[:100]:
            if part.get_filename():
                attachments.append(
                    {
                        "filename": part.get_filename(),
                        "mime_type": part.get_content_type(),
                        "size": len(part.get_payload(decode=True) or b""),
                    }
                )
            elif part.get_content_type() in {"text/plain", "text/html"}:
                payload_bytes = part.get_payload(decode=True)
                body = (payload_bytes if isinstance(payload_bytes, bytes) else b"").decode(
                    part.get_content_charset() or "utf-8", errors="replace"
                )
                (text_parts if part.get_content_type() == "text/plain" else html_parts).append(body)
    else:
        payload = message.get("payload", {})
        headers = {
            str(h.get("name", "")).lower(): str(h.get("value", ""))
            for h in payload.get("headers", [])
        }
        stack = [payload]
        visited = 0
        while stack and visited < 100:
            part = stack.pop()
            visited += 1
            stack.extend(reversed(part.get("parts", [])))
            body = part.get("body", {})
            if part.get("filename"):
                attachments.append(
                    {
                        "filename": part["filename"],
                        "mime_type": part.get("mimeType"),
                        "size": body.get("size", 0),
                        "attachment_id": body.get("attachmentId"),
                    }
                )
            elif body.get("data") and part.get("mimeType") in {"text/plain", "text/html"}:
                value = decode_base64url(body["data"]).decode("utf-8", errors="replace")
                (text_parts if part["mimeType"] == "text/plain" else html_parts).append(value)
    text = "\n".join(text_parts) if text_parts else html_to_text("\n".join(html_parts))
    return {
        "id": message.get("id"),
        "thread_id": message.get("threadId"),
        "subject": headers.get("subject", ""),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "cc": headers.get("cc", ""),
        "bcc": headers.get("bcc", ""),
        "date": headers.get("date", ""),
        "message_id_header": headers.get("message-id", ""),
        "references": headers.get("references", ""),
        "text": text[:max_chars],
        "body_text": text[:max_chars],
        "truncated": len(text) > max_chars,
        "labels": message.get("labelIds", []),
        "attachments": attachments,
        "untrusted": True,
    }
