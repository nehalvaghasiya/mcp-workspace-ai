from mcp_workspace_common.contracts import Risk, ToolDefinition

from mcp_drive.schemas.share_file import ShareFile


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="drive.share_file",
        description="Share one selected Drive file with an explicit email address and reader, commenter, or writer role; preview notification effects.",
        input_model=ShareFile,
        risk=Risk.EXTERNAL_EFFECT,
        scopes=("https://www.googleapis.com/auth/drive",),
    )
