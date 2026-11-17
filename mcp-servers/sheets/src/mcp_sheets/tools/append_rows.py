from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_sheets.schemas.write_range import WriteRange


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="sheets.append_rows",
        description="Append rows inside an approved bounded A1 range, refusing overflow or occupied target cells.",
        input_model=WriteRange,
        risk=Risk.ACCOUNT_WRITE,
        scopes=("https://www.googleapis.com/auth/spreadsheets",),
        scope_alternatives=(
            ("https://www.googleapis.com/auth/spreadsheets",),
            ("https://www.googleapis.com/auth/drive",),
            ("https://www.googleapis.com/auth/drive.file",),
        ),
    )
