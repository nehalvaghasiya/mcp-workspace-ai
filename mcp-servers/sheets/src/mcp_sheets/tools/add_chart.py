from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_sheets.schemas.add_chart import AddChart


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="sheets.add_chart",
        description="Create a basic chart from an approved bounded A1 range.",
        input_model=AddChart,
        risk=Risk.ACCOUNT_WRITE,
        scopes=("https://www.googleapis.com/auth/spreadsheets",),
        scope_alternatives=(
            ("https://www.googleapis.com/auth/spreadsheets",),
            ("https://www.googleapis.com/auth/drive",),
            ("https://www.googleapis.com/auth/drive.file",),
        ),
    )
