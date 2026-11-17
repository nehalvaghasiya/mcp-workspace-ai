from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_slides.schemas.presentation_id import PresentationId


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="slides.get_presentation",
        description="Read a Google Slides presentation including slide IDs, text, shapes and tables.",
        input_model=PresentationId,
        risk=Risk.READ,
        scopes=("https://www.googleapis.com/auth/presentations.readonly",),
        scope_alternatives=(
            ("https://www.googleapis.com/auth/presentations.readonly",),
            ("https://www.googleapis.com/auth/presentations",),
            ("https://www.googleapis.com/auth/drive",),
            ("https://www.googleapis.com/auth/drive.readonly",),
            ("https://www.googleapis.com/auth/drive.file",),
        ),
    )
