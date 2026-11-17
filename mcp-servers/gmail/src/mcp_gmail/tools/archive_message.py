from mcp_workspace_common.contracts import GMAIL, Risk, ToolDefinition

from mcp_gmail.schemas.message_id import MessageId


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="gmail.archive_message",
        description="Archive one selected message by removing its INBOX label after exact approval.",
        input_model=MessageId,
        risk=Risk.ACCOUNT_WRITE,
        scopes=(GMAIL + "modify",),
    )
