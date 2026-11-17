from mcp_workspace_common.contracts import DRIVE, Risk, ToolDefinition

from mcp_drive.schemas.folder import Folder


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="drive.list_folder",
        description="drive: list folder. Access is limited to the signed-in user's authorized data.",
        input_model=Folder,
        risk=Risk.READ,
        scopes=(DRIVE,),
        scope_alternatives=(
            (DRIVE,),
            ("https://www.googleapis.com/auth/drive.readonly",),
            ("https://www.googleapis.com/auth/drive",),
        ),
    )
