from mcp_documents.schemas.report_block import ReportBlock
from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field, model_validator


class CreateDocument(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    parent_id: str | None = Field(default=None, max_length=200, pattern=r"^[A-Za-z0-9_-]+$")
    blocks: list[ReportBlock] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def bounded(self) -> "CreateDocument":
        if len(self.model_dump_json().encode()) > 500000:
            raise ValueError("Document content exceeds 500000 bytes")
        return self
