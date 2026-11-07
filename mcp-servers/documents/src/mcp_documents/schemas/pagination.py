from mcp_workspace_common.contracts import StrictModel
from pydantic import Field


class Pagination(StrictModel):
    max_results: int = Field(default=20, ge=1, le=50)
