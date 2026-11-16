from mcp_workspace_common.contracts import DRIVE, Risk, ToolDefinition

from mcp_drive.schemas.find_operation import FindOperation


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="drive.find_operation",
        description="Inspect files already created by a recorded workspace operation after an uncertain write; never repeats the write.",
        input_model=FindOperation,
        risk=Risk.READ,
        scopes=(DRIVE,),
        scope_alternatives=(
            (DRIVE,),
            ("https://www.googleapis.com/auth/drive.readonly",),
            ("https://www.googleapis.com/auth/drive",),
        ),
    )
