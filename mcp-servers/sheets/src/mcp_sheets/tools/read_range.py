from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_sheets.schemas.range_request import RangeRequest


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="sheets.read_range",
        description="Read a bounded A1 spreadsheet range, preserving formulas and typed values.",
        input_model=RangeRequest,
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
