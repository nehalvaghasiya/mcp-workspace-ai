from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


def summarize(results: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for result in results:
        data = result.get("data", {})
        for key in ("messages", "events", "files"):
            records = data.get(key, [])
            if isinstance(records, list) and records:
                parts.append(
                    f"{len(records)} {key}: "
                    + "; ".join(
                        str(
                            row.get("subject")
                            or row.get("title")
                            or row.get("summary")
                            or row.get("name")
                            or row.get("id", "")
                        )
                        for row in records[:5]
                    )
                )
                if key == "events":
                    for row in records[:5]:
                        left, right = row.get("start", {}), row.get("end", {})
                        parts.append(
                            f"{row.get('title') or row.get('summary', 'Meeting')}: {left.get('dateTime', left.get('date', 'unknown'))} to {right.get('dateTime', right.get('date', 'unknown'))}"
                        )
                if key == "messages":
                    for row in records[:3]:
                        if row.get("body_text"):
                            parts.append(str(row["body_text"])[:700])
        for key in ("text", "content", "body_text"):
            if isinstance(data.get(key), str):
                parts.append(data[key][:1200])
        if "calendars" in data and data.get("time_min"):
            unavailable = [name for name, row in data["calendars"].items() if row.get("errors")]
            if unavailable:
                parts.append("Availability is incomplete for: " + ", ".join(unavailable))
            else:
                intervals = sorted(
                    (datetime.fromisoformat(row["start"]), datetime.fromisoformat(row["end"]))
                    for calendar in data["calendars"].values()
                    for row in calendar.get("busy", [])
                )
                cursor, limit = (
                    datetime.fromisoformat(data["time_min"]),
                    datetime.fromisoformat(data["time_max"]),
                )
                slots: list[str] = []
                for left, right in [*intervals, (limit, limit)]:
                    while cursor + timedelta(minutes=30) <= left and len(slots) < 3:
                        slots.append(
                            f"{cursor.isoformat()} – {(cursor + timedelta(minutes=30)).isoformat()}"
                        )
                        cursor += timedelta(minutes=30)
                    cursor = max(cursor, right)
                parts.append(
                    "Available 30-minute suggestions (not booked): "
                    + ("; ".join(slots) or "No matching slot")
                )
    return "\n\n".join(parts) or "No matching source records were returned."
