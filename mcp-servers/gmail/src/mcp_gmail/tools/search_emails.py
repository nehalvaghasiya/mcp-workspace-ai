from mcp_workspace_common.contracts import GMAIL, Risk, ToolDefinition
from mcp_workspace_common.schemas.search import Search


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="gmail.search_messages",
        description="gmail: search messages. Access is limited to the signed-in user's authorized data.",
        input_model=Search,
        risk=Risk.READ,
        scopes=(GMAIL + "readonly",),
    )
