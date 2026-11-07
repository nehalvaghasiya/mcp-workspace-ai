import contextvars
from typing import Any

caller: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("caller")
