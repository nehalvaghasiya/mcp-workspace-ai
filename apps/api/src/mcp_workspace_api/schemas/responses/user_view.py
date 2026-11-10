from mcp_workspace_api.contracts import StrictModel


class UserView(StrictModel):
    id: str
    display_name: str
    email: str
    timezone: str
