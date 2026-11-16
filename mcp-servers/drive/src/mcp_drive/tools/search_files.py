from mcp_workspace_common.contracts import DRIVE, Risk, ToolDefinition

from mcp_drive.schemas.file_search import FileSearch


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="drive.search_files",
        description="Search existing accessible Drive files with pagination. Use list_drives then drive_id to search a shared drive. Follow next_page_token and report incomplete_search rather than claiming exhaustive results.",
        input_model=FileSearch,
        risk=Risk.READ,
        scopes=(DRIVE,),
        scope_alternatives=(
            (DRIVE,),
            ("https://www.googleapis.com/auth/drive.readonly",),
            ("https://www.googleapis.com/auth/drive",),
        ),
    )
