from mcp_workspace_common.contracts import GMAIL, Risk, ToolDefinition

from mcp_gmail.schemas.message_id import MessageId


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="gmail.get_message",
        description=(
            "Read one message from the signed-in user's Gmail using a message_id returned by gmail.search_messages. "
            "Use format='full' (the default) or 'text' to retrieve its body for summarization; 'metadata' omits the body."
        ),
        input_model=MessageId,
        risk=Risk.READ,
        scopes=(GMAIL + "readonly",),
    )
