from mcp_calendar.server import tool_definitions as calendar_tools
from mcp_demo.server import tool_definitions as demo_tools
from mcp_documents.server import tool_definitions as document_tools
from mcp_drive.server import tool_definitions as drive_tools
from mcp_gmail.server import tool_definitions as gmail_tools
from mcp_workspace_common.contracts import ToolDefinition


def tool_definitions() -> dict[str, ToolDefinition]:
    result: dict[str, ToolDefinition] = {}
    for definitions in (
        gmail_tools(),
        calendar_tools(),
        drive_tools(),
        document_tools(),
        demo_tools(),
    ):
        if set(result) & set(definitions):
            raise ValueError("Duplicate trusted tool definition")
        result.update(definitions)
    return result
