from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field


class PresentationId(StrictModel):
    presentation_id: str = Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9_-]+$")
