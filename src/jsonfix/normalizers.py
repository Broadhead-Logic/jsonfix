"""Text normalization functions for jsonfix."""

from __future__ import annotations

from .repairs import Repair, RepairKind, create_repair

# Smart/curly quote mappings to straight quotes
SMART_DOUBLE_QUOTES: dict[str, str] = {
    "\u201c": '"',  # Left double quotation mark "
    "\u201d": '"',  # Right double quotation mark "
    "\u201e": '"',  # Double low-9 quotation mark „
    "\u201f": '"',  # Double high-reversed-9 quotation mark ‟
    "\u00ab": '"',  # Left-pointing double angle quotation mark «
    "\u00bb": '"',  # Right-pointing double angle quotation mark »
    "\u2033": '"',  # Double prime ″
    "\u301d": '"',  # Reversed double prime quotation mark 〝
    "\u301e": '"',  # Double prime quotation mark 〞
}

SMART_SINGLE_QUOTES: dict[str, str] = {
    "\u2018": "'",  # Left single quotation mark '
    "\u2019": "'",  # Right single quotation mark '
    "\u201a": "'",  # Single low-9 quotation mark ‚
    "\u201b": "'",  # Single high-reversed-9 quotation mark ‛
    "\u2039": "'",  # Single left-pointing angle quotation mark ‹
    "\u203a": "'",  # Single right-pointing angle quotation mark ›
    "\u2032": "'",  # Prime ′
    "\u0060": "'",  # Grave accent `
    "\u00b4": "'",  # Acute accent ´
}

# Combined mapping for all quote normalizations
ALL_QUOTE_MAPPINGS: dict[str, str] = {**SMART_DOUBLE_QUOTES, **SMART_SINGLE_QUOTES}


def normalize_quotes(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Normalize smart/curly quotes to straight quotes.

    Replaces various Unicode quote characters with their ASCII equivalents.
    Double quote variants become ", single quote variants become '.

    Args:
        text: The input text to normalize
        repair_log: Optional list to append Repair objects to

    Returns:
        Text with smart quotes replaced by straight quotes
    """
    if not text:
        return text

    result_chars: list[str] = []
    i = 0

    while i < len(text):
        char = text[i]

        if char in ALL_QUOTE_MAPPINGS:
            replacement = ALL_QUOTE_MAPPINGS[char]
            result_chars.append(replacement)

            if repair_log is not None:
                repair = create_repair(
                    kind=RepairKind.SMART_QUOTE,
                    text=text,
                    position=i,
                    original=char,
                    replacement=replacement,
                )
                repair_log.append(repair)
        else:
            result_chars.append(char)

        i += 1

    return "".join(result_chars)


def has_smart_quotes(text: str) -> bool:
    """Check if text contains any smart quotes.

    Args:
        text: The text to check

    Returns:
        True if text contains smart quotes that would be normalized
    """
    return any(char in ALL_QUOTE_MAPPINGS for char in text)


def convert_single_quote_strings(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Convert single-quoted strings to double-quoted strings.

    Converts 'string' to "string" when not inside a double-quoted string.
    Handles:
    - Escaped single quotes: \\' → '
    - Double quotes inside: 'he said "hi"' → "he said \\"hi\\""

    Args:
        text: The input text to process
        repair_log: Optional list to append Repair objects to

    Returns:
        Text with single-quoted strings converted to double quotes
    """
    if not text:
        return text

    result: list[str] = []
    i = 0
    in_double_string = False
    escape_next = False

    while i < len(text):
        char = text[i]

        # Handle escape sequences
        if escape_next:
            result.append(char)
            escape_next = False
            i += 1
            continue

        if char == "\\":
            result.append(char)
            escape_next = True
            i += 1
            continue

        # Track double-quoted string boundaries
        if char == '"' and not in_double_string:
            in_double_string = True
            result.append(char)
            i += 1
            continue
        elif char == '"' and in_double_string:
            in_double_string = False
            result.append(char)
            i += 1
            continue

        # Convert single-quoted strings when outside double strings
        if char == "'" and not in_double_string:
            # Find the closing single quote
            start_pos = i
            j = i + 1
            string_content: list[str] = []
            escape_in_single = False

            while j < len(text):
                c = text[j]
                if escape_in_single:
                    if c == "'":
                        # Escaped single quote inside single-quoted string
                        string_content.append("'")
                    elif c == '"':
                        # Escaped double quote - keep the escape
                        string_content.append('\\"')
                    else:
                        # Keep other escapes as-is
                        string_content.append("\\")
                        string_content.append(c)
                    escape_in_single = False
                    j += 1
                    continue

                if c == "\\":
                    escape_in_single = True
                    j += 1
                    continue

                if c == "'":
                    # Found closing quote
                    original = text[start_pos : j + 1]
                    # Escape any unescaped double quotes in the content
                    converted_content = "".join(string_content).replace(
                        '"', '\\"'
                    )
                    # But don't double-escape already escaped quotes
                    converted_content = converted_content.replace('\\\\"', '\\"')
                    replacement = '"' + converted_content + '"'

                    if repair_log is not None:
                        repair = create_repair(
                            kind=RepairKind.SINGLE_QUOTE_STRING,
                            text=text,
                            position=start_pos,
                            original=original,
                            replacement=replacement,
                        )
                        repair_log.append(repair)

                    result.append(replacement)
                    i = j + 1
                    break

                string_content.append(c)
                j += 1
            else:
                # No closing quote found - leave as-is
                result.append(char)
                i += 1
            continue

        result.append(char)
        i += 1

    return "".join(result)


def quote_unquoted_keys(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Add quotes around unquoted object keys.

    Converts {key: value} to {"key": value}.

    Args:
        text: The input text to process
        repair_log: Optional list to append Repair objects to

    Returns:
        Text with unquoted keys quoted
    """
    if not text:
        return text

    result: list[str] = []
    i = 0
    in_string = False
    escape_next = False

    while i < len(text):
        char = text[i]

        # Handle escape sequences
        if escape_next:
            result.append(char)
            escape_next = False
            i += 1
            continue

        if char == "\\" and in_string:
            result.append(char)
            escape_next = True
            i += 1
            continue

        # Track string boundaries
        if char == '"':
            in_string = not in_string
            result.append(char)
            i += 1
            continue

        # Look for unquoted keys after { or ,
        if not in_string and char in "{,":
            result.append(char)
            i += 1

            # Skip whitespace
            while i < len(text) and text[i] in " \t\n\r":
                result.append(text[i])
                i += 1

            if i >= len(text):
                break

            # Check if next is an identifier (unquoted key)
            if text[i].isalpha() or text[i] in "_$":
                key_start = i
                j = i
                # Read identifier: [a-zA-Z_$][a-zA-Z0-9_$]*
                while j < len(text) and (
                    text[j].isalnum() or text[j] in "_$"
                ):
                    j += 1

                # Skip whitespace after identifier
                k = j
                while k < len(text) and text[k] in " \t\n\r":
                    k += 1

                # Check if followed by colon (making it a key)
                if k < len(text) and text[k] == ":":
                    key = text[key_start:j]
                    original = key

                    if repair_log is not None:
                        repair = create_repair(
                            kind=RepairKind.UNQUOTED_KEY,
                            text=text,
                            position=key_start,
                            original=original,
                            replacement=f'"{key}"',
                        )
                        repair_log.append(repair)

                    result.append('"')
                    result.append(key)
                    result.append('"')
                    # Add whitespace between key and colon
                    result.append(text[j:k])
                    i = k
                    continue

            continue

        result.append(char)
        i += 1

    return "".join(result)


# Python literal mappings
PYTHON_LITERALS: dict[str, str] = {
    "True": "true",
    "False": "false",
    "None": "null",
}


def convert_python_literals(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Convert Python literals to JSON equivalents.

    Converts True → true, False → false, None → null.
    Only converts when the literal appears as a standalone value,
    not inside strings.

    Args:
        text: The input text to process
        repair_log: Optional list to append Repair objects to

    Returns:
        Text with Python literals converted to JSON
    """
    if not text:
        return text

    result: list[str] = []
    i = 0
    in_string = False
    escape_next = False

    while i < len(text):
        char = text[i]

        # Handle escape sequences
        if escape_next:
            result.append(char)
            escape_next = False
            i += 1
            continue

        if char == "\\" and in_string:
            result.append(char)
            escape_next = True
            i += 1
            continue

        # Track string boundaries
        if char == '"':
            in_string = not in_string
            result.append(char)
            i += 1
            continue

        # Look for Python literals outside strings
        if not in_string:
            for py_literal, json_literal in PYTHON_LITERALS.items():
                if text[i:].startswith(py_literal):
                    # Check word boundaries
                    before_ok = i == 0 or not text[i - 1].isalnum()
                    after_pos = i + len(py_literal)
                    after_ok = after_pos >= len(text) or not text[
                        after_pos
                    ].isalnum()

                    if before_ok and after_ok:
                        if repair_log is not None:
                            repair = create_repair(
                                kind=RepairKind.PYTHON_LITERAL,
                                text=text,
                                position=i,
                                original=py_literal,
                                replacement=json_literal,
                            )
                            repair_log.append(repair)

                        result.append(json_literal)
                        i += len(py_literal)
                        break
            else:
                result.append(char)
                i += 1
            continue

        result.append(char)
        i += 1

    return "".join(result)


def escape_newlines_in_strings(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Escape literal newlines inside strings.

    Converts literal newline characters to \\n escape sequences.

    Args:
        text: The input text to process
        repair_log: Optional list to append Repair objects to

    Returns:
        Text with newlines in strings escaped
    """
    if not text:
        return text

    result: list[str] = []
    i = 0
    in_string = False
    escape_next = False

    while i < len(text):
        char = text[i]

        # Handle escape sequences
        if escape_next:
            result.append(char)
            escape_next = False
            i += 1
            continue

        if char == "\\" and in_string:
            result.append(char)
            escape_next = True
            i += 1
            continue

        # Track string boundaries
        if char == '"':
            in_string = not in_string
            result.append(char)
            i += 1
            continue

        # Escape literal newlines inside strings
        if in_string and char in "\n\r":
            if repair_log is not None:
                repair = create_repair(
                    kind=RepairKind.UNESCAPED_NEWLINE,
                    text=text,
                    position=i,
                    original=repr(char)[1:-1],  # '\n' or '\r'
                    replacement="\\n" if char == "\n" else "\\r",
                )
                repair_log.append(repair)

            if char == "\n":
                result.append("\\n")
            else:  # \r
                result.append("\\r")
            i += 1
            continue

        result.append(char)
        i += 1

    return "".join(result)


def remove_ellipsis_markers(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Remove truncation markers like ... from arrays/objects.

    Removes '...' or '…' when they appear as array/object elements.

    Args:
        text: The input text to process
        repair_log: Optional list to append Repair objects to

    Returns:
        Text with ellipsis markers removed
    """
    if not text:
        return text

    result: list[str] = []
    i = 0
    in_string = False
    escape_next = False

    while i < len(text):
        char = text[i]

        # Handle escape sequences
        if escape_next:
            result.append(char)
            escape_next = False
            i += 1
            continue

        if char == "\\" and in_string:
            result.append(char)
            escape_next = True
            i += 1
            continue

        # Track string boundaries
        if char == '"':
            in_string = not in_string
            result.append(char)
            i += 1
            continue

        # Look for ellipsis markers outside strings
        if not in_string:
            # Check for ASCII ellipsis ...
            if text[i : i + 3] == "...":
                # Look back to remove preceding comma
                removed = "..."
                start_pos = i

                # Check if there's a comma before (with optional whitespace)
                j = len(result) - 1
                while j >= 0 and result[j] in " \t\n\r":
                    j -= 1
                if j >= 0 and result[j] == ",":
                    # Remove the comma and whitespace
                    while len(result) > j:
                        result.pop()
                    removed = ", ..."

                if repair_log is not None:
                    repair = create_repair(
                        kind=RepairKind.TRUNCATION_MARKER,
                        text=text,
                        position=start_pos,
                        original=removed,
                        replacement="",
                    )
                    repair_log.append(repair)

                i += 3
                # Skip whitespace after ellipsis
                while i < len(text) and text[i] in " \t\n\r":
                    i += 1
                continue

            # Check for Unicode ellipsis …
            if char == "…":
                removed = "…"
                start_pos = i

                # Check if there's a comma before
                j = len(result) - 1
                while j >= 0 and result[j] in " \t\n\r":
                    j -= 1
                if j >= 0 and result[j] == ",":
                    while len(result) > j:
                        result.pop()
                    removed = ", …"

                if repair_log is not None:
                    repair = create_repair(
                        kind=RepairKind.TRUNCATION_MARKER,
                        text=text,
                        position=start_pos,
                        original=removed,
                        replacement="",
                    )
                    repair_log.append(repair)

                i += 1
                # Skip whitespace after ellipsis
                while i < len(text) and text[i] in " \t\n\r":
                    i += 1
                continue

        result.append(char)
        i += 1

    return "".join(result)
