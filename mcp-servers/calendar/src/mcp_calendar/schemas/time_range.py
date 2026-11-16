from __future__ import annotations

from datetime import datetime

from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import model_validator


class TimeRange(StrictModel):
    time_min: str
    time_max: str
    timezone: str = "America/Chicago"

    @model_validator(mode="after")
    def times(self) -> TimeRange:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError:
            raise ValueError("Use a valid IANA timezone") from None
        left, right = datetime.fromisoformat(self.time_min), datetime.fromisoformat(self.time_max)
        if not left.tzinfo or not right.tzinfo or left >= right or (right - left).days > 366:
            raise ValueError(
                "Use an ordered date range with explicit UTC offsets (maximum 366 days)"
            )
        return self
