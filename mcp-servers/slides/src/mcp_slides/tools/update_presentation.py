from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_slides.schemas.update_presentation import UpdatePresentation


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="slides.update_presentation",
        description="Edit selected shape text, replace exact text, append slides or remove selected slides after approval.",
        input_model=UpdatePresentation,
        risk=Risk.DESTRUCTIVE,
        scopes=("https://www.googleapis.com/auth/presentations",),
        scope_alternatives=(
            ("https://www.googleapis.com/auth/presentations",),
            ("https://www.googleapis.com/auth/drive",),
            ("https://www.googleapis.com/auth/drive.file",),
        ),
    )
