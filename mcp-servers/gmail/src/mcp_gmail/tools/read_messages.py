from mcp_workspace_common.contracts import GMAIL, Risk, ToolDefinition

from mcp_gmail.schemas.message_batch import MessageBatch


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="gmail.get_messages",
        description=(
            "Read the full bodies of up to 20 selected Gmail messages in one bounded batch. "
            "Use message_ids returned by gmail.search_messages. Prefer this tool when summarizing "
            "multiple messages; it avoids a separate model round trip per message. "
            "Returns messages in the requested order with individual sources. This tool never modifies mail."
        ),
        input_model=MessageBatch,
        risk=Risk.READ,
        scopes=(GMAIL + "readonly",),
    )
