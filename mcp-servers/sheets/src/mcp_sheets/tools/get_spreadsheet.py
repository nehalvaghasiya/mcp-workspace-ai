from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_sheets.schemas.spreadsheet_id import SpreadsheetId


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="sheets.get_spreadsheet",
        description="Read spreadsheet metadata, tabs and chart identifiers.",
        input_model=SpreadsheetId,
        risk=Risk.READ,
        scopes=("https://www.googleapis.com/auth/spreadsheets.readonly",),
        scope_alternatives=(
            ("https://www.googleapis.com/auth/spreadsheets.readonly",),
            ("https://www.googleapis.com/auth/spreadsheets",),
            ("https://www.googleapis.com/auth/drive",),
            ("https://www.googleapis.com/auth/drive.readonly",),
            ("https://www.googleapis.com/auth/drive.file",),
        ),
    )
