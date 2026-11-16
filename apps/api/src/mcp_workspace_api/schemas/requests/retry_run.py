from pydantic import Field

from mcp_workspace_api.contracts import StrictModel


class RetryRun(StrictModel):
    request_id: str = Field(min_length=1, max_length=100)
