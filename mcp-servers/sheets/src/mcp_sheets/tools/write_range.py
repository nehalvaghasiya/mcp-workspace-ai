from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_sheets.schemas.write_range import WriteRange


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="sheets.write_range",
        description="Write typed values to an approved bounded A1 range. Formula cells must be explicitly typed.",
        input_model=WriteRange,
        risk=Risk.ACCOUNT_WRITE,
        scopes=("https://www.googleapis.com/auth/spreadsheets",),
        scope_alternatives=(
            ("https://www.googleapis.com/auth/spreadsheets",),
            ("https://www.googleapis.com/auth/drive",),
            ("https://www.googleapis.com/auth/drive.file",),
        ),
    )
