from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_sheets.schemas.add_sheet import AddSheet


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="sheets.add_sheet",
        description="Add a named worksheet tab to an existing spreadsheet.",
        input_model=AddSheet,
        risk=Risk.ACCOUNT_WRITE,
        scopes=("https://www.googleapis.com/auth/spreadsheets",),
        scope_alternatives=(
            ("https://www.googleapis.com/auth/spreadsheets",),
            ("https://www.googleapis.com/auth/drive",),
            ("https://www.googleapis.com/auth/drive.file",),
        ),
    )
