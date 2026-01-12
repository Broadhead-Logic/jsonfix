"""Repair types and logging for jsonfix."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class RepairKind(Enum):
    """Types of repairs that can be made during parsing."""

    # V1 repair kinds
    TRAILING_COMMA = auto()
    SINGLE_LINE_COMMENT = auto()
    MULTI_LINE_COMMENT = auto()
    HASH_COMMENT = auto()
    SMART_QUOTE = auto()
    # V2 repair kinds
    SINGLE_QUOTE_STRING = auto()
    UNQUOTED_KEY = auto()
    PYTHON_LITERAL = auto()
    UNESCAPED_NEWLINE = auto()
    MISSING_BRACKET = auto()
    TRUNCATION_MARKER = auto()


@dataclass(frozen=True)
class Repair:
    """Record of a single repair made during parsing.

    Attributes:
        kind: The type of repair (from RepairKind enum)
        position: Character position in original string (0-indexed)
        line: Line number in original string (1-indexed)
        column: Column number in original string (1-indexed)
        original: The original text that was repaired
        replacement: The replacement text (empty string if removed)
        message: Human-readable description of the repair
    """

    kind: RepairKind
    position: int
    line: int
    column: int
    original: str
    replacement: str
    message: str


def _calculate_line_column(text: str, position: int) -> tuple[int, int]:
    """Calculate line and column from absolute position.

    Args:
        text: The full text
        position: Absolute character position (0-indexed)

    Returns:
        Tuple of (line, column) where both are 1-indexed
    """
    if position < 0:
        position = 0
    if position > len(text):
        position = len(text)

    # Count newlines before position
    text_before = text[:position]
    lines = text_before.split("\n")
    line = len(lines)
    column = len(lines[-1]) + 1 if lines else 1

    return line, column


def create_repair(
    kind: RepairKind,
    text: str,
    position: int,
    original: str,
    replacement: str = "",
) -> Repair:
    """Create a Repair object with calculated line/column.

    Args:
        kind: The type of repair
        text: The full original text (for position calculation)
        position: Character position in original string
        original: The original text being repaired
        replacement: The replacement text (default: empty for removal)

    Returns:
        A Repair object with all fields populated
    """
    line, column = _calculate_line_column(text, position)

    # Generate human-readable message based on kind
    if kind == RepairKind.TRAILING_COMMA:
        message = "Removed trailing comma"
    elif kind == RepairKind.SINGLE_LINE_COMMENT:
        # Truncate long comments in message
        comment_preview = original[:30] + "..." if len(original) > 30 else original
        message = f"Removed single-line comment '{comment_preview}'"
    elif kind == RepairKind.MULTI_LINE_COMMENT:
        comment_preview = original[:30] + "..." if len(original) > 30 else original
        message = f"Removed multi-line comment '{comment_preview}'"
    elif kind == RepairKind.HASH_COMMENT:
        comment_preview = original[:30] + "..." if len(original) > 30 else original
        message = f"Removed hash comment '{comment_preview}'"
    elif kind == RepairKind.SMART_QUOTE:
        message = f"Replaced smart quote '{original}' with '{replacement}'"
    elif kind == RepairKind.SINGLE_QUOTE_STRING:
        preview = original[:30] + "..." if len(original) > 30 else original
        message = f"Converted single-quoted string '{preview}' to double quotes"
    elif kind == RepairKind.UNQUOTED_KEY:
        message = f"Added quotes around unquoted key '{original}'"
    elif kind == RepairKind.PYTHON_LITERAL:
        message = f"Converted Python literal '{original}' to JSON '{replacement}'"
    elif kind == RepairKind.UNESCAPED_NEWLINE:
        message = "Escaped literal newline in string"
    elif kind == RepairKind.MISSING_BRACKET:
        message = f"Added missing closing bracket '{replacement}'"
    elif kind == RepairKind.TRUNCATION_MARKER:
        message = f"Removed truncation marker '{original}'"
    else:
        message = f"Repaired: {original} -> {replacement}"

    return Repair(
        kind=kind,
        position=position,
        line=line,
        column=column,
        original=original,
        replacement=replacement,
        message=message,
    )
