from mcp_workspace_api.contracts import StrictModel
from mcp_workspace_api.schemas.responses.message_view import MessageView
from mcp_workspace_api.schemas.responses.run_view import RunView


class ConversationView(StrictModel):
    id: str
    title: str
    messages: list[MessageView]
    runs: list[RunView]
