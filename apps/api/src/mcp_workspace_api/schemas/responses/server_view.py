from mcp_workspace_api.contracts import StrictModel


class ServerView(StrictModel):
    id: str
    name: str
    transport: str
    protocol_version: str
    status: str
