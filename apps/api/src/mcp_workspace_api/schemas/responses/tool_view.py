from pydantic import JsonValue

from mcp_workspace_api.contracts import StrictModel


class ToolView(StrictModel):
    name: str
    server: str
    input_schema: dict[str, JsonValue]
    output_schema: dict[str, JsonValue] | None
    risk: str
    enabled: bool
    digest: str
    description: str
