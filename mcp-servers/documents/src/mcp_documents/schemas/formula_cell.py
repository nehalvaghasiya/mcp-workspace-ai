from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AfterValidator

from mcp_documents.schemas.strict_model import StrictModel
from mcp_documents.validators.formulas import _safe_formula


class FormulaCell(StrictModel):
    type: Literal["formula"]
    value: Annotated[str, AfterValidator(_safe_formula)]
