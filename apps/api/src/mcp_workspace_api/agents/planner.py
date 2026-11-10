from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from mcp_workspace_api.core.security import Denied


def fake_plan(prompt: str, previous: dict[str, Any]) -> list[dict[str, Any]]:
    """Scripted demo routing, explicitly not a measurement of model intelligence."""
    text = prompt.lower()
    if "reschedule" in text and not previous.get("references", {}).get("event"):
        raise Denied(
            "CLARIFICATION_REQUIRED", "Which meeting and absolute date/time should I change?"
        )
    if (
        "send" in text
        and "email" in text
        and "reply" not in text
        and not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]+", prompt)
        and "ignore all rules" not in text
    ):
        raise Denied(
            "CLARIFICATION_REQUIRED", "Provide the exact recipient before drafting an email"
        )
    if "unsupported binary" in text:
        raise Denied("UNSUPPORTED_FORMAT", "This binary format cannot be extracted safely")
    if any(
        word in text for word in ("ignore all rules", "exfiltrate", "credentials", "entire inbox")
    ):
        return []
    steps: list[dict[str, Any]] = []

    def add(tool: str, **args: Any) -> None:
        steps.append({"tool": tool, "arguments": args})

    if "tool" in text and any(word in text for word in ("available", "server", "expose")):
        add("demo.ping")
        return steps
    if "send" in text and any(word in text for word in ("that draft", "draft now", "send now")):
        add("gmail.send_draft", draft_id="$draft")
        return steps
    broad = any(word in text for word in ("morning brief", "cross-app")) or (
        "northstar" in text
        and not any(
            word in text for word in ("mail", "message", "calendar", "meeting", "drive", "proposal")
        )
    )
    mail = broad or any(
        word in text for word in ("email", "mail", "message", "thread", "reply", "alex", "triage")
    )
    calendar = broad or any(
        word in text
        for word in (
            "calendar",
            "meeting",
            "schedule",
            "tomorrow",
            "free time",
            "slots",
            "availability",
        )
    )
    drive = broad or any(word in text for word in ("drive", "proposal", "checklist"))
    if mail:
        query = "nonexistent" if "nonexistent" in text else "launch"
        if "unread" in text:
            query += " is:unread"
        add("gmail.search_messages", query=query, max_results=10)
        add("gmail.get_thread", thread_id="$thread")
    if calendar and "reschedule" not in text:
        start, end = demo_range(text)
        add(
            "calendar.list_events",
            calendar_id="primary",
            time_min=start,
            time_max=end,
            timezone="America/Chicago",
        )
        if any(word in text for word in ("free", "slot", "availability", "conflict", "schedule")):
            add(
                "calendar.query_freebusy",
                calendar_ids=["primary", "team"],
                time_min=datetime.fromisoformat(start)
                .replace(hour=12 if "afternoon" in text else 9)
                .isoformat()
                if "wednesday" in text or "tomorrow" in text
                else "2026-11-11T09:00:00-06:00",
                time_max=datetime.fromisoformat(start)
                .replace(hour=18 if "afternoon" in text else 17)
                .isoformat()
                if "wednesday" in text or "tomorrow" in text
                else "2026-11-11T17:00:00-06:00",
                timezone="America/Chicago",
            )
    if drive:
        add("drive.search_files", query="launch", max_results=10)
        add("drive.read_file", file_id="$file")
    if "reschedule" in text:
        match = re.search(r"\b(\d{1,2})(?::([0-5]\d))?\s*(am|pm)\b", text)
        military = re.search(r"\b([01]\d|2[0-3]):([0-5]\d)\b", text)
        reference = previous.get("references", {})
        if not (match or military) or not reference.get("event_start"):
            raise Denied(
                "CLARIFICATION_REQUIRED",
                "Specify AM/PM or a 24-hour time for the selected timed meeting",
            )
        if match:
            if not 1 <= int(match[1]) <= 12:
                raise Denied("INVALID_ARGUMENT", "Use a valid meeting time")
            hour, minute = int(match[1]) % 12 + (12 if match[3] == "pm" else 0), int(match[2] or 0)
        elif military:
            hour, minute = int(military[1]), int(military[2])
        else:
            raise Denied("CLARIFICATION_REQUIRED", "Specify the meeting time")
        old_start = datetime.fromisoformat(reference["event_start"])
        old_end = datetime.fromisoformat(reference["event_end"])
        new_start = old_start.replace(hour=hour, minute=minute)
        add("calendar.get_event", calendar_id="primary", event_id="$event")
        add(
            "calendar.update_event",
            calendar_id="primary",
            event_id="$event",
            changes={
                "start": new_start.isoformat(),
                "end": (new_start + (old_end - old_start)).isoformat(),
                "timezone": "America/Chicago",
            },
        )
    formats: list[str] = []
    for format_name, words in {
        "docx": ("word", "docx", "action report"),
        "pdf": ("pdf", "decision brief"),
        "xlsx": ("excel", "xlsx", "tracker", "workbook"),
        "pptx": ("powerpoint", "pptx", "slides", "presentation", "deck"),
        "csv": ("csv",),
        "markdown": ("markdown",),
        "html": ("html",),
    }.items():
        if any(word in text for word in words):
            formats.append(format_name)
    if any(word in text for word in ("all four", "same report")):
        formats = ["docx", "pdf", "xlsx", "pptx"]
    elif "csv" in text and "excel" not in text and "xlsx" not in text:
        formats = [format_name for format_name in formats if format_name != "xlsx"]
    if "recap" in text and "save" in text and not formats:
        formats = ["docx"]
    for format_name in formats:
        add(
            "artifact.create_" + format_name,
            format=format_name,
            title="Northstar launch "
            + {"xlsx": "task tracker", "pptx": "presentation"}.get(format_name, "report"),
            blocks=[],
            sheets=[],
            slides=[],
        )
    if "save" in text and "drive" in text and formats:
        add("drive.upload_artifact", artifact_id="$artifact")
    if (
        "draft" in text
        or "reply" in text
        or ("send" in text and "email" in text)
        or ("recap" in text and "email" in text)
    ):
        addresses = re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]+", prompt)
        add(
            "gmail.create_draft",
            to=addresses or ["alex@example.invalid"],
            subject="Northstar launch follow-up",
            body_text="$summary",
            reply_to_message_id="$message",
        )
        if "send" in text and "do not send" not in text and "don't send" not in text:
            add("gmail.send_draft", draft_id="$draft")
    if "create" in text and "event" in text:
        add(
            "calendar.create_event",
            title="Northstar launch status",
            start="2026-11-12T14:00:00-06:00",
            end="2026-11-12T14:30:00-06:00",
            timezone="America/Chicago",
            attendees=[],
        )
    if not steps:
        add("demo.ping")
    return steps


def demo_range(text: str) -> tuple[str, str]:
    """Relative dates use the manifest's frozen clock, never the machine clock."""
    from zoneinfo import ZoneInfo

    text = text.lower()
    start = datetime(2026, 11, 5, tzinfo=ZoneInfo("America/Chicago"))
    end = start + timedelta(days=9)
    if "tomorrow" in text:
        start += timedelta(days=1)
        end = start + timedelta(days=1)
    for index, name in enumerate(
        ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    ):
        if name in text:
            start += timedelta(days=(index - start.weekday()) % 7 or 7)
            end = start + timedelta(days=1)
            break
    if "afternoon" in text:
        start = start.replace(hour=12)
        end = start.replace(hour=18)
    return start.isoformat(), end.isoformat()
