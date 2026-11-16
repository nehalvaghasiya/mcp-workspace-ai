from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_drive.schemas.rename_file import RenameFile


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="drive.rename_file",
        description="Rename one selected existing Drive file after exact approval.",
        input_model=RenameFile,
        risk=Risk.ACCOUNT_WRITE,
        scopes=("https://www.googleapis.com/auth/drive",),
    )
