from mcp_workspace_api.contracts import StrictModel


class ConversationSummary(StrictModel):
    id: str
    title: str
    updated_at: str
