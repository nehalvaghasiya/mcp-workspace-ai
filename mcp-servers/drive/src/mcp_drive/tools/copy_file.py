from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_drive.schemas.copy_file import CopyFile


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="drive.copy_file",
        description="Copy an existing Drive file to the approved name and destination folder.",
        input_model=CopyFile,
        risk=Risk.ACCOUNT_WRITE,
        scopes=("https://www.googleapis.com/auth/drive",),
    )
