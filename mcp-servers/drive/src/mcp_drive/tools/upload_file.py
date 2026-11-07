from mcp_workspace_common.contracts import DRIVE, Risk, ToolDefinition

from mcp_drive.schemas.upload import Upload


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="drive.upload_artifact",
        description="drive: upload artifact. Access is limited to the signed-in user's authorized data.",
        input_model=Upload,
        risk=Risk.ACCOUNT_WRITE,
        scopes=(DRIVE,),
    )
