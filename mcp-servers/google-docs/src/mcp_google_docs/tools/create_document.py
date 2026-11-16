from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_google_docs.schemas.create_document import CreateDocument


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="docs.create_document",
        description="Create a native Google document with headings, paragraphs, bullet lists and tables in an optional Drive folder.",
        input_model=CreateDocument,
        risk=Risk.ACCOUNT_WRITE,
        scopes=("https://www.googleapis.com/auth/documents",),
        scope_alternatives=(
            ("https://www.googleapis.com/auth/drive",),
            ("https://www.googleapis.com/auth/drive.file",),
        ),
    )
