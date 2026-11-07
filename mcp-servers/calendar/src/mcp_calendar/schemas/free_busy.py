from __future__ import annotations

from pydantic import Field

from mcp_calendar.schemas.time_range import TimeRange


class FreeBusy(TimeRange):
    calendar_ids: list[str] = Field(default_factory=lambda: ["primary"], max_length=10)
