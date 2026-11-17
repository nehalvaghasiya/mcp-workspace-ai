from mcp_workspace_common.contracts import GMAIL, Risk, ToolDefinition

from mcp_gmail.schemas.message_id import MessageId


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="gmail.untrash_message",
        description="Restore one selected Gmail message from Trash after exact approval.",
        input_model=MessageId,
        risk=Risk.ACCOUNT_WRITE,
        scopes=(GMAIL + "modify",),
    )
