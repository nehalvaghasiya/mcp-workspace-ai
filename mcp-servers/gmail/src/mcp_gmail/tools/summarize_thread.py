from mcp_workspace_common.contracts import GMAIL, Risk, ToolDefinition

from mcp_gmail.schemas.thread_id import ThreadId


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="gmail.get_thread",
        description="gmail: get thread. Access is limited to the signed-in user's authorized data.",
        input_model=ThreadId,
        risk=Risk.READ,
        scopes=(GMAIL + "readonly",),
    )
