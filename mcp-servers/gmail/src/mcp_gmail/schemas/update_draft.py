from __future__ import annotations

from pydantic import Field

from mcp_gmail.schemas.draft import Draft


class UpdateDraft(Draft):
    draft_id: str = Field(min_length=1, max_length=256)
