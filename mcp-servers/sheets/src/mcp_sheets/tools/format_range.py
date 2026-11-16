from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_sheets.schemas.format_range import FormatRange


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="sheets.format_range",
        description="Apply basic text, background and number formatting to an approved A1 range.",
        input_model=FormatRange,
        risk=Risk.ACCOUNT_WRITE,
        scopes=("https://www.googleapis.com/auth/spreadsheets",),
        scope_alternatives=(
            ("https://www.googleapis.com/auth/spreadsheets",),
            ("https://www.googleapis.com/auth/drive",),
            ("https://www.googleapis.com/auth/drive.file",),
        ),
    )
