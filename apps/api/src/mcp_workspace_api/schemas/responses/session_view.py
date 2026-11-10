from typing import Literal

from mcp_workspace_api.contracts import StrictModel
from mcp_workspace_api.schemas.responses.model_view import ModelView
from mcp_workspace_api.schemas.responses.user_view import UserView


class SessionView(StrictModel):
    user: UserView | None
    csrf_token: str
    mode: Literal["mock", "live"]
    llm: ModelView
