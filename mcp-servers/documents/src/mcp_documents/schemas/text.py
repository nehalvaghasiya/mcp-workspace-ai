from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, Field

from mcp_documents.utils.text import _plain_text

Text = Annotated[str, Field(max_length=10_000), AfterValidator(_plain_text)]

Label = Annotated[str, Field(min_length=1, max_length=200), AfterValidator(_plain_text)]

TableText = Annotated[str, Field(max_length=2_000), AfterValidator(_plain_text)]
