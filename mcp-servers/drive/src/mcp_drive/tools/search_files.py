from mcp_workspace_common.contracts import DRIVE, Risk, ToolDefinition

from mcp_drive.schemas.file_search import FileSearch


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="drive.search_files",
        description="drive: search files. Access is limited to the signed-in user's authorized data.",
        input_model=FileSearch,
        risk=Risk.READ,
        scopes=(DRIVE,),
    )
