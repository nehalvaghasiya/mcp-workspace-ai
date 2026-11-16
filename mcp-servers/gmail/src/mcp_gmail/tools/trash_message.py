from mcp_workspace_common.contracts import GMAIL, Risk, ToolDefinition

from mcp_gmail.schemas.message_id import MessageId


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="gmail.trash_message",
        description="Move one selected Gmail message to Trash after exact approval; does not permanently delete it.",
        input_model=MessageId,
        risk=Risk.DESTRUCTIVE,
        scopes=(GMAIL + "modify",),
    )
