from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_sheets.schemas.create_spreadsheet import CreateSpreadsheet


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="sheets.create_spreadsheet",
        description="Create a native Google spreadsheet with typed worksheets in an optional Drive folder.",
        input_model=CreateSpreadsheet,
        risk=Risk.ACCOUNT_WRITE,
        scopes=("https://www.googleapis.com/auth/spreadsheets",),
        scope_alternatives=(
            ("https://www.googleapis.com/auth/drive",),
            ("https://www.googleapis.com/auth/drive.file",),
        ),
    )
