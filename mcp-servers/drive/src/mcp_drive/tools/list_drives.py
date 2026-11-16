from mcp_workspace_common.contracts import DRIVE, Risk, ToolDefinition

from mcp_drive.schemas.drives import Drives


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="drive.list_drives",
        description="List shared drives accessible to the signed-in account, with pagination.",
        input_model=Drives,
        risk=Risk.READ,
        scopes=(DRIVE,),
        scope_alternatives=(
            (DRIVE,),
            ("https://www.googleapis.com/auth/drive.readonly",),
            ("https://www.googleapis.com/auth/drive",),
        ),
    )
