"""Core parsing logic for jsonfix."""

from __future__ import annotations

import json
import re
import warnings
from typing import IO, Any, Literal

from .normalizers import (
    convert_python_literals,
    convert_single_quote_strings,
    escape_newlines_in_strings,
    normalize_quotes,
    quote_unquoted_keys,
    remove_ellipsis_markers,
)
from .repairs import Repair, RepairKind, create_repair


class RelaxedJSONError(ValueError):
    """Error raised when relaxed JSON parsing fails."""

    pass


def _strip_comments(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Strip comments from JSON text.

    Handles:
    - Single-line comments: // ... (to end of line)
    - Hash comments: # ... (to end of line)
    - Multi-line comments: /* ... */

    Comments inside JSON strings are preserved.

    Args:
        text: JSON text possibly containing comments
        repair_log: Optional list to append Repair objects to

    Returns:
        JSON text with comments removed
    """
    result: list[str] = []
    i = 0
    in_string = False
    escape_next = False

    while i < len(text):
        char = text[i]

        # Handle escape sequences in strings
        if escape_next:
            result.append(char)
            escape_next = False
            i += 1
            continue

        # Track string boundaries
        if char == '"' and not in_string:
            in_string = True
            result.append(char)
            i += 1
            continue
        elif char == '"' and in_string:
            in_string = False
            result.append(char)
            i += 1
            continue
        elif char == "\\" and in_string:
            escape_next = True
            result.append(char)
            i += 1
            continue

        # Only process comments outside strings
        if not in_string:
            # Single-line comment: //
            if char == "/" and i + 1 < len(text) and text[i + 1] == "/":
                # Find end of line
                end = text.find("\n", i)
                if end == -1:
                    end = len(text)
                else:
                    end += 1  # Include the newline in the comment

                comment = text[i:end]
                if repair_log is not None:
                    repair = create_repair(
                        kind=RepairKind.SINGLE_LINE_COMMENT,
                        text=text,
                        position=i,
                        original=comment.rstrip("\n"),
                    )
                    repair_log.append(repair)

                # Replace comment with whitespace to preserve positions
                # (but we'll just skip it for now)
                i = end
                continue

            # Hash comment: #
            if char == "#":
                # Find end of line
                end = text.find("\n", i)
                if end == -1:
                    end = len(text)
                else:
                    end += 1  # Include the newline

                comment = text[i:end]
                if repair_log is not None:
                    repair = create_repair(
                        kind=RepairKind.HASH_COMMENT,
                        text=text,
                        position=i,
                        original=comment.rstrip("\n"),
                    )
                    repair_log.append(repair)

                i = end
                continue

            # Multi-line comment: /* ... */
            if char == "/" and i + 1 < len(text) and text[i + 1] == "*":
                # Find closing */
                end = text.find("*/", i + 2)
                if end == -1:
                    raise RelaxedJSONError(
                        f"Unclosed multi-line comment at position {i}"
                    )
                end += 2  # Include the */

                comment = text[i:end]
                if repair_log is not None:
                    repair = create_repair(
                        kind=RepairKind.MULTI_LINE_COMMENT,
                        text=text,
                        position=i,
                        original=comment,
                    )
                    repair_log.append(repair)

                # Replace with single space to separate tokens
                result.append(" ")
                i = end
                continue

        result.append(char)
        i += 1

    return "".join(result)


def _remove_trailing_commas(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Remove trailing commas from JSON text.

    Handles trailing commas in objects and arrays:
    - {"a": 1,} -> {"a": 1}
    - [1, 2, 3,] -> [1, 2, 3]

    Args:
        text: JSON text possibly containing trailing commas
        repair_log: Optional list to append Repair objects to

    Returns:
        JSON text with trailing commas removed
    """
    # Pattern to match trailing comma before ] or }
    # This needs to handle whitespace and newlines between comma and closing bracket
    # We need to track string boundaries to avoid modifying commas in strings

    result: list[str] = []
    i = 0
    in_string = False
    escape_next = False

    while i < len(text):
        char = text[i]

        # Handle escape sequences in strings
        if escape_next:
            result.append(char)
            escape_next = False
            i += 1
            continue

        # Track string boundaries
        if char == '"' and not in_string:
            in_string = True
            result.append(char)
            i += 1
            continue
        elif char == '"' and in_string:
            in_string = False
            result.append(char)
            i += 1
            continue
        elif char == "\\" and in_string:
            escape_next = True
            result.append(char)
            i += 1
            continue

        # Only process commas outside strings
        if not in_string and char == ",":
            # Look ahead: is this a trailing comma?
            # Skip whitespace and check if next non-whitespace is ] or }
            j = i + 1
            while j < len(text) and text[j] in " \t\n\r":
                j += 1

            if j < len(text) and text[j] in "]}":
                # This is a trailing comma - skip it
                if repair_log is not None:
                    repair = create_repair(
                        kind=RepairKind.TRAILING_COMMA,
                        text=text,
                        position=i,
                        original=",",
                    )
                    repair_log.append(repair)
                i += 1
                continue

        result.append(char)
        i += 1

    return "".join(result)


def _auto_close_brackets(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Add missing closing brackets at end of input.

    Tracks bracket nesting and adds any missing closing brackets
    at the end of the string.

    Args:
        text: JSON text possibly with missing closing brackets
        repair_log: Optional list to append Repair objects to

    Returns:
        JSON text with missing closing brackets added
    """
    if not text:
        return text

    # Stack of opening brackets
    bracket_stack: list[str] = []
    i = 0
    in_string = False
    escape_next = False

    while i < len(text):
        char = text[i]

        # Handle escape sequences
        if escape_next:
            escape_next = False
            i += 1
            continue

        if char == "\\" and in_string:
            escape_next = True
            i += 1
            continue

        # Track string boundaries
        if char == '"':
            in_string = not in_string
            i += 1
            continue

        # Track brackets outside strings
        if not in_string:
            if char == "{":
                bracket_stack.append("{")
            elif char == "[":
                bracket_stack.append("[")
            elif char == "}":
                if bracket_stack and bracket_stack[-1] == "{":
                    bracket_stack.pop()
            elif char == "]":
                if bracket_stack and bracket_stack[-1] == "[":
                    bracket_stack.pop()

        i += 1

    # Add missing closing brackets
    if not bracket_stack:
        return text

    closing_brackets: list[str] = []
    end_position = len(text)

    for bracket in reversed(bracket_stack):
        if bracket == "{":
            closing = "}"
        else:
            closing = "]"

        closing_brackets.append(closing)

        if repair_log is not None:
            repair = create_repair(
                kind=RepairKind.MISSING_BRACKET,
                text=text,
                position=end_position,
                original="",
                replacement=closing,
            )
            repair_log.append(repair)

    return text + "".join(closing_brackets)


def loads_relaxed(
    s: str,
    *,
    strict: bool = False,
    # V1 options
    allow_trailing_commas: bool = True,
    allow_comments: bool = True,
    normalize_quotes: bool = True,
    # V2 options
    allow_single_quote_strings: bool = True,
    allow_unquoted_keys: bool = True,
    convert_python_literals: bool = True,
    escape_newlines: bool = True,
    auto_close_brackets: bool = True,
    remove_ellipsis: bool = True,
    # Common options
    repair_log: list[Repair] | None = None,
    on_repair: Literal["ignore", "warn", "error"] = "ignore",
) -> Any:
    """Parse a relaxed JSON string into Python objects.

    This function extends standard JSON parsing to accept common relaxations:
    - Trailing commas in objects and arrays
    - Comments (// single-line, # hash, /* multi-line */)
    - Smart/curly quotes normalized to straight quotes
    - Single-quoted strings converted to double-quoted (V2)
    - Unquoted keys quoted (V2)
    - Python literals converted to JSON (True→true, None→null) (V2)
    - Literal newlines in strings escaped (V2)
    - Missing closing brackets auto-added (V2)
    - Truncation markers (...) removed (V2)

    Args:
        s: JSON string (possibly with relaxed syntax)
        strict: If True, disable all relaxations and use standard json.loads
        allow_trailing_commas: Allow trailing commas in arrays/objects
        allow_comments: Allow // # and /* */ comments
        normalize_quotes: Convert smart quotes to straight quotes
        allow_single_quote_strings: Convert 'string' to "string"
        allow_unquoted_keys: Quote unquoted keys like {key: 1}
        convert_python_literals: Convert True/False/None to true/false/null
        escape_newlines: Escape literal newlines in strings
        auto_close_brackets: Add missing closing brackets at end
        remove_ellipsis: Remove truncation markers like ...
        repair_log: Optional list to collect Repair objects documenting fixes
        on_repair: Action when repair needed:
            - "ignore": Parse silently (default)
            - "warn": Emit warnings via warnings.warn()
            - "error": Raise ValueError on first repair needed

    Returns:
        Parsed Python object (dict, list, str, int, float, bool, or None)

    Raises:
        json.JSONDecodeError: If the JSON is invalid even after relaxations
        ValueError: If on_repair="error" and repairs are needed
    """
    if on_repair not in ("ignore", "warn", "error"):
        raise ValueError(f"Invalid on_repair value: {on_repair!r}")

    # Strict mode: use standard json.loads directly
    if strict:
        return json.loads(s)

    # Collect repairs in a local list if on_repair needs it
    local_repairs: list[Repair] = []
    actual_log = repair_log if repair_log is not None else local_repairs

    processed = s

    # Step 0: Strip BOM if present
    if processed.startswith("\ufeff"):
        processed = processed[1:]

    # Step 1: Normalize smart quotes (V1)
    if normalize_quotes:
        # Import here to use the function (avoiding name collision with parameter)
        from .normalizers import normalize_quotes as _normalize_quotes

        processed = _normalize_quotes(processed, actual_log)

    # Step 2: Convert single-quote strings (V2)
    if allow_single_quote_strings:
        processed = convert_single_quote_strings(processed, actual_log)

    # Step 3: Quote unquoted keys (V2)
    if allow_unquoted_keys:
        processed = quote_unquoted_keys(processed, actual_log)

    # Step 4: Convert Python literals (V2)
    if convert_python_literals:
        # Import here to use the function (avoiding name collision with parameter)
        from .normalizers import convert_python_literals as _convert_python_literals

        processed = _convert_python_literals(processed, actual_log)

    # Step 5: Escape newlines in strings (V2)
    if escape_newlines:
        processed = escape_newlines_in_strings(processed, actual_log)

    # Step 6: Remove ellipsis markers (V2)
    if remove_ellipsis:
        processed = remove_ellipsis_markers(processed, actual_log)

    # Step 7: Strip comments (V1)
    if allow_comments:
        processed = _strip_comments(processed, actual_log)

    # Step 8: Auto-close brackets (V2 - must be before trailing comma removal)
    # so that '{"a": 1,' becomes '{"a": 1,}' and then trailing comma is removed
    if auto_close_brackets:
        processed = _auto_close_brackets(processed, actual_log)

    # Step 9: Remove trailing commas (V1 - must be after auto-close)
    if allow_trailing_commas:
        processed = _remove_trailing_commas(processed, actual_log)

    # Check if any repairs were made
    if actual_log:
        if on_repair == "error":
            repair = actual_log[0]
            raise ValueError(
                f"Repair needed at line {repair.line}, column {repair.column}: "
                f"{repair.message}"
            )
        elif on_repair == "warn":
            for repair in actual_log:
                warnings.warn(
                    f"JSON repair at line {repair.line}: {repair.message}",
                    category=UserWarning,
                    stacklevel=2,
                )

    # Parse the processed JSON
    try:
        return json.loads(processed)
    except json.JSONDecodeError as e:
        # Re-raise with original error
        raise e


def load_relaxed(
    fp: IO[str],
    **kwargs: Any,
) -> Any:
    """Parse a relaxed JSON file into Python objects.

    Like loads_relaxed but reads from a file-like object.

    Args:
        fp: File-like object with a read() method
        **kwargs: Additional arguments passed to loads_relaxed

    Returns:
        Parsed Python object
    """
    return loads_relaxed(fp.read(), **kwargs)


def can_parse(s: str) -> bool:
    """Check if a string can be parsed with relaxations.

    Args:
        s: String to check

    Returns:
        True if the string can be parsed (with relaxations)
    """
    try:
        loads_relaxed(s)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def get_repairs(s: str) -> list[Repair]:
    """Get list of repairs needed to parse a string.

    This parses the string and returns all repairs that would be made,
    without raising errors.

    Args:
        s: JSON string to analyze

    Returns:
        List of Repair objects describing fixes needed
    """
    repairs: list[Repair] = []
    try:
        loads_relaxed(s, repair_log=repairs, on_repair="ignore")
    except (json.JSONDecodeError, ValueError):
        # Even if parsing fails, return any repairs collected
        pass
    return repairs
