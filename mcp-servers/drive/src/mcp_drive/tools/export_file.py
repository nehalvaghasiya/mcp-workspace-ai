from mcp_workspace_common.contracts import DRIVE, Risk, ToolDefinition

from mcp_drive.schemas.export_file import ExportFile


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="drive.export_file",
        description="Export a selected native Google Doc, Sheet, or Slides file to a downloadable PDF or supported Office format.",
        input_model=ExportFile,
        risk=Risk.READ,
        scopes=(DRIVE,),
        scope_alternatives=(
            (DRIVE,),
            ("https://www.googleapis.com/auth/drive.readonly",),
            ("https://www.googleapis.com/auth/drive",),
        ),
    )
