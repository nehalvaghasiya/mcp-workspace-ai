from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field


class TextReplacement(StrictModel):
    find: str = Field(min_length=1, max_length=10000)
    replacement: str = Field(max_length=50000)
    match_case: bool = True
