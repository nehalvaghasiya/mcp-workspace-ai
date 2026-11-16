from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_drive.schemas.file_id import FileId


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="drive.trash_file",
        description="Move one selected Drive file into Trash after exact approval; does not permanently delete it.",
        input_model=FileId,
        risk=Risk.DESTRUCTIVE,
        scopes=("https://www.googleapis.com/auth/drive",),
    )
