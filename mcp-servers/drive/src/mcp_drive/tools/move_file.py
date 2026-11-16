from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_drive.schemas.move_file import MoveFile


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="drive.move_file",
        description="Move one selected existing Drive file into an approved folder.",
        input_model=MoveFile,
        risk=Risk.ACCOUNT_WRITE,
        scopes=("https://www.googleapis.com/auth/drive",),
    )
