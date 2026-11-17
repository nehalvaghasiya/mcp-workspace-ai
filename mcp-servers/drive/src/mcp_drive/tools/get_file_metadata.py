from mcp_workspace_common.contracts import DRIVE, Risk, ToolDefinition

from mcp_drive.schemas.file_id import FileId


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="drive.get_file_metadata",
        description="drive: get file metadata. Access is limited to the signed-in user's authorized data.",
        input_model=FileId,
        risk=Risk.READ,
        scopes=(DRIVE,),
        scope_alternatives=(
            (DRIVE,),
            ("https://www.googleapis.com/auth/drive.readonly",),
            ("https://www.googleapis.com/auth/drive",),
        ),
    )
