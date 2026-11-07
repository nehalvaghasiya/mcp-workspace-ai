from mcp_workspace_common.contracts import DRIVE, Risk, ToolDefinition

from mcp_drive.schemas.read_file import ReadFile


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="drive.read_file",
        description="drive: read file. Access is limited to the signed-in user's authorized data.",
        input_model=ReadFile,
        risk=Risk.READ,
        scopes=(DRIVE,),
    )
