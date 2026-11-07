from __future__ import annotations

from mcp_workspace_common.schemas.strict_model import StrictModel
from pydantic import Field, model_validator


class Draft(StrictModel):
    to: list[str] = Field(min_length=1, max_length=20)
    cc: list[str] = Field(default_factory=list, max_length=20)
    bcc: list[str] = Field(default_factory=list, max_length=20)
    subject: str = Field(max_length=500)
    body_text: str = Field(max_length=20000)
    reply_to_message_id: str | None = None

    @model_validator(mode="after")
    def addresses(self) -> Draft:
        import re

        for address in self.to + self.cc + self.bcc:
            if not re.fullmatch(r"[^\s@<>\r\n]+@[^\s@<>\r\n]+\.[^\s@<>\r\n]+", address):
                raise ValueError("Provide explicit valid recipient addresses")
        if "\n" in self.subject or "\r" in self.subject:
            raise ValueError("Subject cannot contain header separators")
        return self
