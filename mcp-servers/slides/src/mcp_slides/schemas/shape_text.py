from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field


class ShapeText(StrictModel):
    object_id: str = Field(min_length=5, max_length=200, pattern=r"^[A-Za-z0-9_:-]+$")
    text: str = Field(max_length=50000)
