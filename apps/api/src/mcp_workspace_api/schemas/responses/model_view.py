from mcp_workspace_api.contracts import StrictModel


class ModelView(StrictModel):
    provider: str
    model: str
    consented: bool
