from mcp_workspace_common.contracts import DRIVE, Risk, ToolDefinition

from mcp_drive.schemas.create_folder import CreateFolder


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="drive.create_folder",
        description="drive: create folder. Access is limited to the signed-in user's authorized data.",
        input_model=CreateFolder,
        risk=Risk.ACCOUNT_WRITE,
        scopes=(DRIVE,),
    )
