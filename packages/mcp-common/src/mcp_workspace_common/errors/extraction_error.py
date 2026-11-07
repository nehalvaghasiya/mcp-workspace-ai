from __future__ import annotations


class ExtractionError(ValueError):
    """Safe public error; never include underlying parser errors or document text."""
