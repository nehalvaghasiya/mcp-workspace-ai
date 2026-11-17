from mcp_workspace_api.core.security import Denied


class TransientModelError(Denied):
    def __init__(self) -> None:
        super().__init__(
            "PROVIDER_UNAVAILABLE",
            "The model gateway encountered a temporary upstream failure. Retrieved information is saved.",
        )
