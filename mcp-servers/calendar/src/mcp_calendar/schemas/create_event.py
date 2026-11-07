from __future__ import annotations

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

    @model_validator(mode="after")
    def times(self) -> CreateEvent:
        TimeRange(time_min=self.start, time_max=self.end, timezone=self.timezone)
        return self
