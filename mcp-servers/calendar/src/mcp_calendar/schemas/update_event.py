from __future__ import annotations

from pydantic import JsonValue, model_validator

from mcp_calendar.schemas.event_id import EventId


class UpdateEvent(EventId):
    changes: dict[str, JsonValue]
    etag: str | None = None

    @model_validator(mode="after")
    def safe_changes(self) -> UpdateEvent:
        if not self.changes or set(self.changes) - {
            "title",
            "start",
            "end",
            "timezone",
            "attendees",
            "description",
            "location",
        }:
            raise ValueError("Unsupported event changes")
        return self
