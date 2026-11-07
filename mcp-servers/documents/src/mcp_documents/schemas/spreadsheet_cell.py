from __future__ import annotations

from typing import Annotated

from pydantic import Field

from mcp_documents.schemas.date_cell import DateCell
from mcp_documents.schemas.formula_cell import FormulaCell
from mcp_documents.schemas.number_cell import NumberCell
from mcp_documents.schemas.string_cell import StringCell

SpreadsheetCell = Annotated[
    StringCell | NumberCell | DateCell | FormulaCell, Field(discriminator="type")
]
