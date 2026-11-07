from mcp_workspace_common.contracts import GMAIL, Risk, ToolDefinition

from mcp_gmail.schemas.message_id import MessageId


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="gmail.get_message",
        description="gmail: get message. Access is limited to the signed-in user's authorized data.",
        input_model=MessageId,
        risk=Risk.READ,
        scopes=(GMAIL + "readonly",),
    )
