from __future__ import annotations

from typing import Annotated

from pydantic import Field

from mcp_documents.schemas.bullet_list import BulletList
from mcp_documents.schemas.heading import Heading
from mcp_documents.schemas.paragraph_block import ParagraphBlock
from mcp_documents.schemas.table_block import TableBlock

ReportBlock = Annotated[
    Heading | ParagraphBlock | TableBlock | BulletList, Field(discriminator="type")
]
