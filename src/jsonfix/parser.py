"""Core parsing logic for jsonfix."""

from __future__ import annotations

import json
import re
import warnings
from typing import IO, Any, Literal

from .normalizers import (
    convert_single_quote_strings,
    escape_control_characters,
    escape_newlines_in_strings,
    extract_json_from_text,
    fix_missing_colons,
    fix_missing_commas,
    fix_unescaped_backslash as _fix_unescaped_backslash,
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
                # Check if this is a URL protocol (e.g., https://)
                # URL protocols have : immediately before //
                if i > 0 and text[i - 1] == ":":
                    # This is likely a URL, not a comment
                    result.append(char)
                    i += 1
                    continue

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
    # V3 options (LLM-specific)
    extract_json: bool = True,
    remove_markdown_fences: bool = True,
    fix_unescaped_quotes: bool = True,
    # V3 options (Structural)
    fix_missing_colon: bool = True,
    fix_missing_comma: bool = True,
    escape_control_chars: bool = True,
    fix_unescaped_backslash: bool = True,
    # V3 options (Edge cases)
    convert_javascript_values: bool = True,
    convert_number_formats: bool = True,
    remove_double_commas: bool = True,
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
    - JSON extracted from preamble/postamble text (V3)
    - Markdown code fences removed (V3)
    - Unescaped quotes in strings fixed (V3)
    - Missing colons inserted between keys and values (V3)
    - Missing commas inserted between elements (V3)
    - Control characters escaped (tabs, etc.) (V3)
    - Unescaped backslashes fixed (V3)
    - JavaScript values converted (NaN, Infinity, undefined → null) (V3)
    - Non-decimal number formats converted (0xFF, 0o777, 0b1010) (V3)
    - Double/empty commas removed (V3)

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
        extract_json: Extract JSON from surrounding text (preamble/postamble)
        remove_markdown_fences: Remove ```json code fences
        fix_unescaped_quotes: Escape unescaped quotes in strings
        fix_missing_colon: Insert missing colons between keys and values
        fix_missing_comma: Insert missing commas between elements
        escape_control_chars: Escape control characters in strings
        fix_unescaped_backslash: Escape invalid backslash sequences
        convert_javascript_values: Convert NaN, Infinity, undefined to null
        convert_number_formats: Convert 0xFF, 0o777, 0b1010 to decimal
        remove_double_commas: Remove double/empty commas
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

    # Step 0.1: Remove markdown fences (V3 - must be first to unwrap fenced JSON)
    if remove_markdown_fences:
        from .normalizers import remove_markdown_fences as _remove_markdown_fences

        processed = _remove_markdown_fences(processed, actual_log)

    # Step 0.2: Extract JSON from surrounding text (V3 - after fences, before other processing)
    if extract_json:
        processed = extract_json_from_text(processed, actual_log)

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

    # Step 5: Fix unescaped backslashes (V3) - FIRST in escape processing
    # so that user-provided backslashes are escaped before other escape
    # sequences are added by subsequent steps
    if fix_unescaped_backslash:
        processed = _fix_unescaped_backslash(processed, actual_log)

    # Step 5.1: Escape newlines in strings (V2) - after backslash fix
    if escape_newlines:
        processed = escape_newlines_in_strings(processed, actual_log)

    # Step 5.2: Escape control characters (V3) - after backslash fix
    # This adds proper escape sequences for actual control chars
    if escape_control_chars:
        processed = escape_control_characters(processed, actual_log)

    # Step 6: Remove ellipsis markers (V2)
    if remove_ellipsis:
        processed = remove_ellipsis_markers(processed, actual_log)

    # Step 7: Strip comments (V1) - must be before other structural fixes
    # so comments don't confuse the heuristics
    if allow_comments:
        processed = _strip_comments(processed, actual_log)

    # Step 7.1: Convert non-decimal number formats (V3 - hex, octal, binary → decimal)
    # MUST run before fix_missing_colons/commas so those normalizers see valid
    # decimal numbers instead of misinterpreting 0xFF as two tokens.
    if convert_number_formats:
        from .normalizers import convert_number_formats as _convert_number_formats

        processed = _convert_number_formats(processed, actual_log)

    # Step 7.2: Convert JavaScript values (V3 - NaN, Infinity, undefined → null)
    # MUST run before fix_missing_colons/commas so those normalizers see valid
    # null values instead of unknown identifiers like "NaN".
    if convert_javascript_values:
        from .normalizers import convert_javascript_values as _convert_js_values

        processed = _convert_js_values(processed, actual_log)

    # Step 7.3: Fix missing colons (V3) - structural, establishes key-value structure
    # so that '{"name" "John"}' becomes '{"name": "John"}'
    # Runs after number/JS conversion so values are recognized correctly.
    if fix_missing_colon:
        processed = fix_missing_colons(processed, actual_log)

    # Step 7.4: Fix unescaped quotes (V3) - AFTER colons, BEFORE commas
    # After colons are in place, we can identify string boundaries.
    # Must run before fix_missing_commas so comma fixer sees valid string boundaries.
    # Example: '{"text": "He said "hello" today"}' needs quotes fixed first.
    if fix_unescaped_quotes:
        from .normalizers import fix_unescaped_quotes as _fix_unescaped_quotes

        processed = _fix_unescaped_quotes(processed, actual_log)

    # Step 7.5: Fix missing commas (V3) - structural, AFTER quote/number fixing
    # Now that strings have proper boundaries and numbers are decimal, we can
    # safely detect missing commas.
    if fix_missing_comma:
        processed = fix_missing_commas(processed, actual_log)

    # Step 8: Auto-close brackets (V2 - must be before trailing comma removal)
    # so that '{"a": 1,' becomes '{"a": 1,}' and then trailing comma is removed
    if auto_close_brackets:
        processed = _auto_close_brackets(processed, actual_log)

    # Step 9: Remove trailing commas (V1 - must be after auto-close)
    if allow_trailing_commas:
        processed = _remove_trailing_commas(processed, actual_log)

    # Step 10: Remove double/empty commas (V3 - edge case cleanup)
    if remove_double_commas:
        from .normalizers import remove_double_commas as _remove_double_commas

        processed = _remove_double_commas(processed, actual_log)

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
