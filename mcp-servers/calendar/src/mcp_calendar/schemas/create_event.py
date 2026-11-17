from __future__ import annotations

import re
from datetime import date

from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field, model_validator

from mcp_calendar.schemas.time_range import TimeRange


class CreateEvent(StrictModel):
    calendar_id: str = "primary"
    title: str = Field(min_length=1, max_length=500)
    start: str
    end: str
    timezone: str = "America/Chicago"
    attendees: list[str] = Field(default_factory=list, max_length=20)
    description: str = Field(default="", max_length=20000)
    location: str = Field(default="", max_length=1000)
    recurrence: list[str] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def times(self) -> CreateEvent:
        if len(self.start) == 10 and len(self.end) == 10:
            from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

            try:
                ZoneInfo(self.timezone)
            except ZoneInfoNotFoundError:
                raise ValueError("Use a valid IANA timezone") from None
            start, end = date.fromisoformat(self.start), date.fromisoformat(self.end)
            if end <= start or (end - start).days > 366:
                raise ValueError(
                    "All-day event end is exclusive and must follow start within 366 days"
                )
        else:
            TimeRange(time_min=self.start, time_max=self.end, timezone=self.timezone)
        for address in self.attendees:
            if not re.fullmatch(r"[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+", address):
                raise ValueError("Provide explicit valid attendee email addresses")
        if any(
            len(rule) > 1000 or not re.fullmatch(r"(?:RRULE|RDATE|EXDATE):[^\r\n]+", rule)
            for rule in self.recurrence
        ):
            raise ValueError("Use bounded RFC recurrence rules without header separators")
        return self
