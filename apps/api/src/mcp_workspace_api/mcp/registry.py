from mcp_calendar.server import tool_definitions as calendar_tools
from mcp_demo.server import tool_definitions as demo_tools
from mcp_documents.server import tool_definitions as document_tools
from mcp_drive.server import tool_definitions as drive_tools
from mcp_gmail.server import tool_definitions as gmail_tools
from mcp_workspace_common.contracts import ToolDefinition


def tool_definitions(mode: str = "mock") -> dict[str, ToolDefinition]:
    result: dict[str, ToolDefinition] = {}
    definitions_list = [
        gmail_tools(include_live=mode == "live"),
        calendar_tools(),
        drive_tools(include_live=mode == "live"),
        document_tools(),
    ]
    if mode == "live":
        from mcp_google_docs.server import tool_definitions as docs_tools
        from mcp_sheets.server import tool_definitions as sheets_tools
        from mcp_slides.server import tool_definitions as slides_tools

        definitions_list.extend((docs_tools(), sheets_tools(), slides_tools()))
    else:
        definitions_list.append(demo_tools())
    for definitions in definitions_list:
        if set(result) & set(definitions):
            raise ValueError("Duplicate trusted tool definition")
        result.update(definitions)
    return result
