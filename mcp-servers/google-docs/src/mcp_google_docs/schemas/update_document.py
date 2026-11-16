from mcp_documents.schemas.report_block import ReportBlock
from pydantic import Field, model_validator

from mcp_google_docs.schemas.document_id import DocumentId
from mcp_google_docs.schemas.text_replacement import TextReplacement


class UpdateDocument(DocumentId):
    append_blocks: list[ReportBlock] = Field(default_factory=list, max_length=100)
    replace_text: list[TextReplacement] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def bounded(self) -> "UpdateDocument":
        if not self.append_blocks and not self.replace_text:
            raise ValueError("Provide text replacements or content to append")
        if len(self.model_dump_json().encode()) > 500000:
            raise ValueError("Document changes exceed 500000 bytes")
        return self
