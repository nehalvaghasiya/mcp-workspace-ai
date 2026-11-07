from __future__ import annotations

from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field


class DraftId(StrictModel):
    draft_id: str = Field(min_length=1, max_length=256)
