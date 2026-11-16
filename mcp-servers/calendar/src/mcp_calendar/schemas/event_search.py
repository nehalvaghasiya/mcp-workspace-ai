from __future__ import annotations

from pydantic import Field

from mcp_calendar.schemas.time_range import TimeRange


class EventSearch(TimeRange):
    calendar_id: str = "primary"
    max_results: int = Field(default=20, ge=1, le=50)
    page_token: str | None = None
    query: str | None = Field(default=None, max_length=1000)
