from mcp_workspace_api.contracts import StrictModel


class SettingsView(StrictModel):
    provider: str
    provider_url: str
    model: str
    llm_consent: bool
    timezone: str
