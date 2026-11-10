from mcp_workspace_api.contracts import SourceRef, StrictModel


class ArtifactView(StrictModel):
    id: str
    title: str
    format: str
    mime_type: str
    size: int
    sha256: str
    created_at: str
    validated: bool
    sources: list[SourceRef]
    download_url: str
