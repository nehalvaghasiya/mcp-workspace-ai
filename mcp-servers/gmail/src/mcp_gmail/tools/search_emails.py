from mcp_workspace_common.contracts import GMAIL, Risk, ToolDefinition
from mcp_workspace_common.schemas.search import Search


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="gmail.search_messages",
        description=(
            "Search the signed-in user's Gmail using the required query in Gmail search syntax. "
            "For the latest inbox messages, use query='in:inbox' and max_results equal to the requested count. "
            "Accepted arguments are query, max_results, and optional page_token; there is no order_by argument. "
            "Results include metadata and snippets. For multiple selected messages, use gmail.get_messages "
            "with their message_ids to read all bodies in one step before summarizing. "
            "Use gmail.get_message for a single selected message."
        ),
        input_model=Search,
        risk=Risk.READ,
        scopes=(GMAIL + "readonly",),
    )
