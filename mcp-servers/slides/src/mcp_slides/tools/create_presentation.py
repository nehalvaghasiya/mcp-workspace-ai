from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_slides.schemas.create_presentation import CreatePresentation


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="slides.create_presentation",
        description="Create a native Google Slides deck with titles, body text, bullet lists, tables and speaker notes.",
        input_model=CreatePresentation,
        risk=Risk.ACCOUNT_WRITE,
        scopes=("https://www.googleapis.com/auth/presentations",),
        scope_alternatives=(
            ("https://www.googleapis.com/auth/drive",),
            ("https://www.googleapis.com/auth/drive.file",),
        ),
    )
