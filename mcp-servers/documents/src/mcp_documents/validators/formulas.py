from __future__ import annotations

import re

from mcp_documents.constants import MAX_ROWS


def _safe_formula(value: str) -> str:
    """Allow only local cell references, numbers, arithmetic and numeric functions.

    No quoted strings, URLs, sheet/workbook links, named ranges, DDE, volatile
    functions, or external-data functions are accepted. Cell ranges are bounded.
    """
    if not value.startswith("=") or len(value) > 500:
        raise ValueError("Formula must start with '=' and contain at most 500 characters")
    pattern = r"\s*(SUM|AVERAGE|MIN|MAX|COUNT|ROUND|ABS|\$?[A-Z]{1,3}\$?[1-9][0-9]{0,3}|[0-9]+(?:\.[0-9]+)?|[()+*/,:-])"
    position = 1
    depth = 0
    tokens: list[str] = []
    while position < len(value):
        match = re.match(pattern, value[position:], flags=re.ASCII)
        if match is None:
            raise ValueError("Formula contains an unsupported token or function")
        part = match.group(1)
        tokens.append(part)
        depth += (part == "(") - (part == ")")
        if depth < 0 or depth > 20:
            raise ValueError("Unbalanced or deeply nested formula")
        position += match.end()
    if depth != 0 or not tokens:
        raise ValueError("Unbalanced or empty formula")
    for index, lexeme in enumerate(tokens):
        if lexeme in {"SUM", "AVERAGE", "MIN", "MAX", "COUNT", "ROUND", "ABS"}:
            if index + 1 == len(tokens) or tokens[index + 1] != "(":
                raise ValueError("Function must have arguments")
        reference = re.fullmatch(r"\$?([A-Z]+)\$?([0-9]+)", lexeme)
        if reference:
            column = 0
            for character in reference.group(1):
                column = column * 26 + ord(character) - ord("A") + 1
            if column > 50 or int(reference.group(2)) > MAX_ROWS + 1:
                raise ValueError("Formula cell reference exceeds sheet bounds")
    # Parse the restricted expression grammar as well as checking its tokens.
    cursor = 0

    def expression() -> None:
        nonlocal cursor
        term()
        while cursor < len(tokens) and tokens[cursor] in {"+", "-"}:
            cursor += 1
            term()

    def term() -> None:
        nonlocal cursor
        atom()
        while cursor < len(tokens) and tokens[cursor] in {"*", "/"}:
            cursor += 1
            atom()

    def atom() -> None:
        nonlocal cursor
        if cursor >= len(tokens):
            raise ValueError("Formula is missing an operand")
        lexeme = tokens[cursor]
        cursor += 1
        if lexeme in {"+", "-"}:
            atom()
        elif lexeme == "(":
            expression()
            consume(")")
        elif lexeme in {"SUM", "AVERAGE", "MIN", "MAX", "COUNT", "ROUND", "ABS"}:
            consume("(")
            count = 1
            expression()
            while cursor < len(tokens) and tokens[cursor] == ",":
                cursor += 1
                count += 1
                expression()
            consume(")")
            if lexeme == "ABS" and count != 1 or lexeme == "ROUND" and count != 2:
                raise ValueError("Formula function has invalid argument count")
        elif re.fullmatch(r"\$?[A-Z]{1,3}\$?[1-9][0-9]{0,3}", lexeme):
            if cursor < len(tokens) and tokens[cursor] == ":":
                cursor += 1
                if cursor >= len(tokens) or not re.fullmatch(
                    r"\$?[A-Z]{1,3}\$?[1-9][0-9]{0,3}", tokens[cursor]
                ):
                    raise ValueError("Range must contain two cell references")
                cursor += 1
        elif not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", lexeme):
            raise ValueError("Formula contains an invalid operand")

    def consume(expected: str) -> None:
        nonlocal cursor
        if cursor >= len(tokens) or tokens[cursor] != expected:
            raise ValueError("Formula expression is incomplete")
        cursor += 1

    expression()
    if cursor != len(tokens):
        raise ValueError("Formula contains an unexpected token")
    return value
