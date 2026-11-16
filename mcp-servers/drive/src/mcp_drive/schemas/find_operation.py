from __future__ import annotations

from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field


class FindOperation(StrictModel):
    operation_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
