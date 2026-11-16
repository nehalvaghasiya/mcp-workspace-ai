from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_google_docs.schemas.update_document import UpdateDocument


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="docs.update_document",
        description="Replace exact text or append structured content to the selected Google document tab after approval.",
        input_model=UpdateDocument,
        risk=Risk.ACCOUNT_WRITE,
        scopes=("https://www.googleapis.com/auth/documents",),
        scope_alternatives=(
            ("https://www.googleapis.com/auth/documents",),
            ("https://www.googleapis.com/auth/drive",),
            ("https://www.googleapis.com/auth/drive.file",),
        ),
    )
