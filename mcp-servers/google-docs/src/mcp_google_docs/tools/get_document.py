from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_google_docs.schemas.document_id import DocumentId


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="docs.get_document",
        description="Read a Google document, including its tabs, paragraphs, lists and tables.",
        input_model=DocumentId,
        risk=Risk.READ,
        scopes=("https://www.googleapis.com/auth/documents.readonly",),
        scope_alternatives=(
            ("https://www.googleapis.com/auth/documents.readonly",),
            ("https://www.googleapis.com/auth/documents",),
            ("https://www.googleapis.com/auth/drive",),
            ("https://www.googleapis.com/auth/drive.readonly",),
            ("https://www.googleapis.com/auth/drive.file",),
        ),
    )
