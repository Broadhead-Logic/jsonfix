"""Text normalization functions for jsonfix."""

from __future__ import annotations

import re

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


# =============================================================================
# V3 normalizers (LLM-specific)
# =============================================================================


def remove_markdown_fences(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Remove markdown code fences from around JSON.

    Handles:
    - ```json ... ```
    - ```javascript ... ```
    - ```js ... ```
    - ``` ... ``` (plain fence)

    Args:
        text: The input text possibly wrapped in markdown fences
        repair_log: Optional list to append Repair objects to

    Returns:
        Text with markdown fences removed
    """
    if not text:
        return text

    # Pattern to match markdown fence at start
    # Allows: ```json, ```JSON, ```javascript, ```js, ``` (with optional space)
    fence_start_pattern = re.compile(
        r'^(\s*)```\s*(?:json|javascript|js)?\s*\n',
        re.IGNORECASE
    )

    # Check for opening fence
    match = fence_start_pattern.match(text)
    if not match:
        return text

    # Find the closing fence
    start_pos = match.end()
    fence_end_pattern = re.compile(r'\n?\s*```\s*$', re.MULTILINE)
    end_match = fence_end_pattern.search(text, start_pos)

    if end_match:
        # Extract content between fences
        content = text[start_pos:end_match.start()]
        extracted = content.strip()
    else:
        # No closing fence - extract content after opening fence
        content = text[start_pos:]
        extracted = content.strip()

    if repair_log is not None:
        repair = create_repair(
            kind=RepairKind.MARKDOWN_FENCE_REMOVED,
            text=text,
            position=0,
            original=text,
            replacement=extracted,
        )
        repair_log.append(repair)

    return extracted


def extract_json_from_text(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Extract JSON from text with surrounding preamble/postamble.

    LLMs often wrap JSON output with text like:
    - "Here is the JSON: {...}"
    - "{...} Let me know if you need changes."
    - "Based on your request:\n{...}\nHope this helps!"

    This function extracts the JSON by finding the first complete
    JSON object or array, handling nested structures correctly.

    Note: Does NOT extract if text starts with JSON comments (// # /*),
    as those should be processed by the comment stripper instead.

    Args:
        text: Text that may contain JSON with surrounding text
        repair_log: Optional list to append Repair objects to

    Returns:
        Extracted JSON string, or original text if no extraction needed
    """
    if not text:
        return text

    original_text = text
    text = text.strip()

    # Don't extract if text starts with JSON comment markers
    # These should be processed by the comment stripper, not treated as preamble
    if text.startswith('//') or text.startswith('#') or text.startswith('/*'):
        return text

    # Find the first { or [
    json_start = -1
    for i, char in enumerate(text):
        if char in '{[':
            json_start = i
            break

    if json_start == -1:
        # No JSON structure found
        return text

    # Find the matching closing bracket
    opening = text[json_start]
    closing = '}' if opening == '{' else ']'

    # Track bracket nesting, accounting for strings
    bracket_count = 0
    in_string = False
    escape_next = False
    json_end = -1

    for i in range(json_start, len(text)):
        char = text[i]

        if escape_next:
            escape_next = False
            continue

        if char == '\\' and in_string:
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == opening:
            bracket_count += 1
        elif char == closing:
            bracket_count -= 1
            if bracket_count == 0:
                json_end = i + 1
                break

    if json_end == -1:
        # No matching closing bracket - return from json_start to end
        extracted = text[json_start:]
        has_postamble = False
    else:
        # Check if postamble starts with a comment marker
        # If so, include it so the comment stripper can handle it
        postamble_raw = text[json_end:]
        postamble = postamble_raw.strip()

        # Check if postamble is actually a comment (should be processed by comment stripper)
        if postamble.startswith('//') or postamble.startswith('#') or postamble.startswith('/*'):
            # Include the postamble - it's a comment, not plain text
            extracted = text[json_start:]
            has_postamble = False  # Don't log as extraction, let comment stripper log it
        else:
            extracted = text[json_start:json_end]
            has_postamble = bool(postamble)

    has_preamble = json_start > 0

    # Only log repair if we actually extracted something (preamble or non-comment postamble)
    if has_preamble or has_postamble:
        if repair_log is not None:
            preamble = text[:json_start] if json_start > 0 else ""
            repair = create_repair(
                kind=RepairKind.JSON_EXTRACTED,
                text=original_text,
                position=0,
                original=preamble,
                replacement="",
            )
            repair_log.append(repair)

    return extracted


# =============================================================================
# V3 normalizers (Structural)
# =============================================================================


# Valid JSON escape characters (after backslash)
VALID_JSON_ESCAPES = set('"\\bfnrtu/')


def fix_missing_colons(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Insert missing colons between keys and values in objects.

    Fixes patterns like:
    - {"key" "value"} → {"key": "value"}
    - {"key" 123} → {"key": 123}
    - {"key" true} → {"key": true}

    Args:
        text: JSON text possibly missing colons
        repair_log: Optional list to append Repair objects to

    Returns:
        Text with missing colons inserted
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

        if char == '\\' and in_string:
            result.append(char)
            escape_next = True
            i += 1
            continue

        # Track string boundaries
        if char == '"':
            if not in_string:
                in_string = True
                result.append(char)
                i += 1
                continue
            else:
                # Closing quote - check if we need to insert a colon
                in_string = False
                result.append(char)
                i += 1

                # Look ahead: skip whitespace
                j = i
                while j < len(text) and text[j] in ' \t\n\r':
                    j += 1

                if j >= len(text):
                    continue

                next_char = text[j]

                # Check if we're in an object context and missing a colon
                # Colon is needed if next char starts a value: " { [ digit - or true/false/null
                if next_char == ':':
                    # Colon already present
                    continue

                # Check if next char could be a value start
                is_value_start = (
                    next_char == '"' or  # String value
                    next_char == '{' or  # Object value
                    next_char == '[' or  # Array value
                    next_char.isdigit() or  # Number
                    next_char == '-' or  # Negative number
                    text[j:].startswith('true') or
                    text[j:].startswith('false') or
                    text[j:].startswith('null')
                )

                if is_value_start:
                    # Check context - are we likely after a key?
                    # Look back in result to see if we're after a { or ,
                    # followed by a string (key)
                    k = len(result) - 1
                    # Skip back past the closing quote we just added
                    if k >= 0 and result[k] == '"':
                        k -= 1
                    # Skip back past string content
                    while k >= 0 and result[k] != '"':
                        k -= 1
                    # Now at opening quote of potential key
                    if k >= 0 and result[k] == '"':
                        k -= 1
                        # Skip whitespace
                        while k >= 0 and result[k] in ' \t\n\r':
                            k -= 1
                        # Check if preceded by { or ,
                        if k >= 0 and result[k] in '{,':
                            # This is a key without colon - insert colon
                            if repair_log is not None:
                                repair = create_repair(
                                    kind=RepairKind.MISSING_COLON,
                                    text=text,
                                    position=i,
                                    original="",
                                    replacement=":",
                                )
                                repair_log.append(repair)
                            result.append(':')
                            # Add the whitespace between key and value
                            while i < j:
                                result.append(text[i])
                                i += 1
                        # Also check if preceded by a value (number, bool, null, closing bracket)
                        # This handles {"a" 1 "b" 2} where "b" comes after the value 1
                        elif k >= 0 and (result[k].isdigit() or result[k] in '}]"' or
                                          ''.join(result[max(0,k-3):k+1]).endswith(('true', 'false', 'null'))):
                            # Check if we're in an object context
                            depth = 0
                            in_obj = False
                            for c in result:
                                if c == '{':
                                    depth += 1
                                    in_obj = True
                                elif c == '[':
                                    depth += 1
                                    in_obj = False
                                elif c == '}':
                                    depth -= 1
                                elif c == ']':
                                    depth -= 1
                            if in_obj and depth > 0:
                                # We're in an object and this key follows a value
                                if repair_log is not None:
                                    repair = create_repair(
                                        kind=RepairKind.MISSING_COLON,
                                        text=text,
                                        position=i,
                                        original="",
                                        replacement=":",
                                    )
                                    repair_log.append(repair)
                                result.append(':')
                                while i < j:
                                    result.append(text[i])
                                    i += 1
                continue

        result.append(char)
        i += 1

    return "".join(result)


def fix_missing_commas(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Insert missing commas between elements in arrays and objects.

    Fixes patterns like:
    - [1 2 3] → [1, 2, 3]
    - {"a": 1 "b": 2} → {"a": 1, "b": 2}

    Args:
        text: JSON text possibly missing commas
        repair_log: Optional list to append Repair objects to

    Returns:
        Text with missing commas inserted
    """
    if not text:
        return text

    result: list[str] = []
    i = 0
    in_string = False
    escape_next = False
    # Track what we just saw (to know when comma is needed)
    just_saw_value = False
    brace_stack: list[str] = []  # Track [ and { nesting

    while i < len(text):
        char = text[i]

        # Handle escape sequences
        if escape_next:
            result.append(char)
            escape_next = False
            i += 1
            continue

        if char == '\\' and in_string:
            result.append(char)
            escape_next = True
            i += 1
            continue

        # Track string boundaries
        if char == '"' and not in_string:
            # Check if we need to insert comma before this string
            if just_saw_value and brace_stack:
                if repair_log is not None:
                    repair = create_repair(
                        kind=RepairKind.MISSING_COMMA,
                        text=text,
                        position=i,
                        original="",
                        replacement=",",
                    )
                    repair_log.append(repair)
                result.append(',')
                result.append(' ')

            in_string = True
            result.append(char)
            i += 1
            just_saw_value = False
            continue
        elif char == '"' and in_string:
            in_string = False
            result.append(char)
            i += 1
            just_saw_value = True
            continue

        if in_string:
            result.append(char)
            i += 1
            continue

        # Handle structure characters
        if char in '{[':
            if just_saw_value and brace_stack:
                if repair_log is not None:
                    repair = create_repair(
                        kind=RepairKind.MISSING_COMMA,
                        text=text,
                        position=i,
                        original="",
                        replacement=",",
                    )
                    repair_log.append(repair)
                result.append(',')
                result.append(' ')

            brace_stack.append(char)
            result.append(char)
            i += 1
            just_saw_value = False
            continue

        if char in '}]':
            if brace_stack:
                brace_stack.pop()
            result.append(char)
            i += 1
            just_saw_value = True
            continue

        if char == ',':
            result.append(char)
            i += 1
            just_saw_value = False
            continue

        if char == ':':
            result.append(char)
            i += 1
            just_saw_value = False
            continue

        # Whitespace
        if char in ' \t\n\r':
            result.append(char)
            i += 1
            continue

        # Numbers, booleans, null
        if char.isdigit() or char == '-':
            # Check if we need comma before this number
            if just_saw_value and brace_stack:
                if repair_log is not None:
                    repair = create_repair(
                        kind=RepairKind.MISSING_COMMA,
                        text=text,
                        position=i,
                        original="",
                        replacement=",",
                    )
                    repair_log.append(repair)
                result.append(',')
                result.append(' ')

            # Parse the number
            j = i
            if text[j] == '-':
                j += 1
            while j < len(text) and (text[j].isdigit() or text[j] in '.eE+-'):
                j += 1
            result.append(text[i:j])
            i = j
            just_saw_value = True
            continue

        # true, false, null
        for literal in ('true', 'false', 'null'):
            if text[i:].startswith(literal):
                if just_saw_value and brace_stack:
                    if repair_log is not None:
                        repair = create_repair(
                            kind=RepairKind.MISSING_COMMA,
                            text=text,
                            position=i,
                            original="",
                            replacement=",",
                        )
                        repair_log.append(repair)
                    result.append(',')
                    result.append(' ')

                result.append(literal)
                i += len(literal)
                just_saw_value = True
                break
        else:
            result.append(char)
            i += 1

    return "".join(result)


def escape_control_characters(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Escape control characters in strings.

    Fixes patterns like:
    - Literal tab → \\t
    - Literal carriage return → \\r
    - Literal form feed → \\f
    - Literal backspace → \\b
    - Other control chars (0x00-0x1F except \\n) → removed or \\uXXXX

    Note: Newlines are handled separately by escape_newlines_in_strings.

    Args:
        text: JSON text with possible control characters
        repair_log: Optional list to append Repair objects to

    Returns:
        Text with control characters escaped
    """
    if not text:
        return text

    # Mapping of control characters to their escape sequences
    CONTROL_CHAR_ESCAPES = {
        '\t': '\\t',   # Tab
        '\r': '\\r',   # Carriage return (also handled by newline escaper)
        '\f': '\\f',   # Form feed
        '\b': '\\b',   # Backspace
    }

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

        if char == '\\' and in_string:
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

        # Handle control characters inside strings
        if in_string:
            if char in CONTROL_CHAR_ESCAPES:
                escape_seq = CONTROL_CHAR_ESCAPES[char]
                if repair_log is not None:
                    repair = create_repair(
                        kind=RepairKind.CONTROL_CHARACTER,
                        text=text,
                        position=i,
                        original=char,
                        replacement=escape_seq,
                    )
                    repair_log.append(repair)
                result.append(escape_seq)
                i += 1
                continue

            # Handle other control characters (0x00-0x1F except newline)
            if ord(char) < 0x20 and char not in '\n\r':
                # Remove or escape as \uXXXX
                escape_seq = f'\\u{ord(char):04x}'
                if repair_log is not None:
                    repair = create_repair(
                        kind=RepairKind.CONTROL_CHARACTER,
                        text=text,
                        position=i,
                        original=char,
                        replacement=escape_seq,
                    )
                    repair_log.append(repair)
                result.append(escape_seq)
                i += 1
                continue

        result.append(char)
        i += 1

    return "".join(result)


def fix_unescaped_backslash(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Fix unescaped backslashes in strings.

    For LLM output, backslashes in strings are usually unintentional (like Windows
    paths). This function escapes all lone backslashes (not part of \\\\) to ensure
    they are treated as literal backslash characters.

    Args:
        text: JSON text with possible unescaped backslashes
        repair_log: Optional list to append Repair objects to

    Returns:
        Text with unescaped backslashes fixed
    """
    if not text:
        return text

    result: list[str] = []
    i = 0
    in_string = False
    escape_next = False

    while i < len(text):
        char = text[i]

        # Track string boundaries
        if char == '"' and not escape_next:
            in_string = not in_string
            result.append(char)
            i += 1
            continue

        if in_string:
            if escape_next:
                # We're after a backslash - the next char is being escaped
                # This is intentional escape sequence (\\, \", etc.) - keep as is
                escape_next = False
                result.append(char)
                i += 1
                continue

            if char == '\\':
                # Check what follows
                if i + 1 < len(text):
                    next_char = text[i + 1]

                    # Valid JSON escape sequences that should be preserved:
                    # \\, \", \/, \b, \f, \n, \r, \t, \uXXXX
                    if next_char == '\\':
                        # Already escaped backslash (\\) - keep as is
                        result.append(char)
                        escape_next = True
                        i += 1
                        continue
                    elif next_char == '"':
                        # Escaped quote (\") - keep as is
                        result.append(char)
                        escape_next = True
                        i += 1
                        continue
                    elif next_char in 'bfnrt/':
                        # Valid JSON escape sequences - but check for Windows path patterns
                        # If the string looks like a Windows path (X:\...), escape all backslashes
                        # Check: is this a Windows path pattern?
                        # Look back from current position to see if we're in a path context
                        is_windows_path = False
                        # Find the start of the current string
                        string_content_start = -1
                        for back_idx in range(len(result) - 1, -1, -1):
                            if result[back_idx] == '"':
                                string_content_start = back_idx + 1
                                break
                        if string_content_start >= 0:
                            # Get the string content so far
                            string_so_far = ''.join(result[string_content_start:])
                            # Check if it looks like start of Windows path: X:\ or X:/
                            if len(string_so_far) >= 2:
                                if (string_so_far[0].isalpha() and
                                        string_so_far[1] == ':'):
                                    is_windows_path = True

                        if is_windows_path:
                            # In Windows path context - escape the backslash
                            if repair_log is not None:
                                repair = create_repair(
                                    kind=RepairKind.UNESCAPED_BACKSLASH,
                                    text=text,
                                    position=i,
                                    original='\\',
                                    replacement='\\\\',
                                )
                                repair_log.append(repair)
                            result.append('\\\\')
                            i += 1
                            continue
                        # Otherwise, keep as valid JSON escape
                        result.append(char)
                        escape_next = True
                        i += 1
                        continue
                    elif next_char == 'u':
                        # Check for valid unicode escape \uXXXX (4 hex digits)
                        if i + 5 < len(text):
                            hex_chars = text[i + 2:i + 6]
                            if all(c in '0123456789abcdefABCDEF' for c in hex_chars):
                                # Valid unicode escape - keep as is
                                result.append(char)
                                escape_next = True
                                i += 1
                                continue
                        # Invalid unicode escape (not followed by 4 hex digits)
                        # Fall through to escape the backslash

                    # Any other backslash sequence - escape the backslash
                    # This handles Windows paths like \Users, \q, etc.
                    if repair_log is not None:
                        repair = create_repair(
                            kind=RepairKind.UNESCAPED_BACKSLASH,
                            text=text,
                            position=i,
                            original='\\',
                            replacement='\\\\',
                        )
                        repair_log.append(repair)
                    result.append('\\\\')
                    i += 1
                    continue
                else:
                    # Backslash at end - escape it
                    if repair_log is not None:
                        repair = create_repair(
                            kind=RepairKind.UNESCAPED_BACKSLASH,
                            text=text,
                            position=i,
                            original='\\',
                            replacement='\\\\',
                        )
                        repair_log.append(repair)
                    result.append('\\\\')
                    i += 1
                    continue

        result.append(char)
        i += 1

    return "".join(result)


def fix_unescaped_quotes(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Fix unescaped quotes inside JSON strings.

    LLMs sometimes produce strings with unescaped internal quotes:
    - {"text": "He said "hello" today"}
    - {"text": "The "important" word"}

    This function detects and escapes such quotes.

    Args:
        text: JSON text possibly containing unescaped quotes
        repair_log: Optional list to append Repair objects to

    Returns:
        Text with unescaped quotes properly escaped
    """
    if not text:
        return text

    result: list[str] = []
    i = 0
    in_string = False
    string_start = -1
    escape_next = False

    while i < len(text):
        char = text[i]

        # Handle escape sequences
        if escape_next:
            result.append(char)
            escape_next = False
            i += 1
            continue

        if char == '\\':
            result.append(char)
            if in_string:
                escape_next = True
            i += 1
            continue

        # Track string boundaries
        if char == '"':
            if not in_string:
                # Starting a string
                in_string = True
                string_start = i
                result.append(char)
                i += 1
                continue
            else:
                # We're in a string and found a quote
                # Is this the end of the string, or an unescaped internal quote?

                # Look ahead to determine context
                j = i + 1

                # Skip whitespace
                while j < len(text) and text[j] in ' \t\n\r':
                    j += 1

                if j >= len(text):
                    # End of input - this is the closing quote
                    in_string = False
                    result.append(char)
                    i += 1
                    continue

                next_char = text[j]

                # Check if this looks like end of string
                # End of string is followed by: ] } (array/object close)
                if next_char in ']}':
                    # This is the closing quote
                    in_string = False
                    result.append(char)
                    i += 1
                    continue

                # For comma, need more context - could be end of value or internal quote
                # Look further ahead to see if there's a valid JSON structure
                if next_char == ',':
                    # Look for pattern: ,"key": or ,number or ,true/false/null or ,"string" or ,[
                    k = j + 1
                    while k < len(text) and text[k] in ' \t\n\r':
                        k += 1
                    if k < len(text):
                        after_comma = text[k]
                        # If after comma we see start of key or value, this is closing quote
                        if after_comma == '"':
                            # Check if it's a key (has colon after) or value
                            m = k + 1
                            while m < len(text) and text[m] != '"' and text[m] != '\\':
                                m += 1
                            if m < len(text) and text[m] == '"':
                                # Skip to after the closing quote
                                m += 1
                                while m < len(text) and text[m] in ' \t\n\r':
                                    m += 1
                                if m < len(text) and text[m] == ':':
                                    # It's a key-value, so current quote closes string
                                    in_string = False
                                    result.append(char)
                                    i += 1
                                    continue
                        elif after_comma in '{[' or after_comma.isdigit() or after_comma == '-':
                            # Start of object, array, or number - closing quote
                            in_string = False
                            result.append(char)
                            i += 1
                            continue
                        elif text[k:].startswith(('true', 'false', 'null')):
                            # Boolean or null - closing quote
                            in_string = False
                            result.append(char)
                            i += 1
                            continue
                    # Otherwise, might be internal quote - check if more text follows
                    # that looks like sentence continuation
                    # Look for more characters before the next quote
                    temp_k = k
                    text_chars = 0
                    while temp_k < len(text) and text[temp_k] != '"':
                        if text[temp_k].isalpha():
                            text_chars += 1
                        temp_k += 1
                    if text_chars > 3:
                        # There's meaningful text after comma - probably internal quote
                        if repair_log is not None:
                            repair = create_repair(
                                kind=RepairKind.UNESCAPED_QUOTE,
                                text=text,
                                position=i,
                                original='"',
                                replacement='\\"',
                            )
                            repair_log.append(repair)
                        result.append('\\')
                        result.append('"')
                        i += 1
                        continue
                    else:
                        # Short or no text - probably closing quote
                        in_string = False
                        result.append(char)
                        i += 1
                        continue

                # For colon, check if it's part of object key
                if next_char == ':':
                    # This is end of a key string
                    in_string = False
                    result.append(char)
                    i += 1
                    continue

                # Check if followed by another quote (which would start a new key/value)
                if next_char == '"':
                    # Could be end of string followed by next string
                    # Or unescaped quote
                    # We need to scan past the next string to see what follows
                    # j points to the opening quote of the potential next string
                    k = j + 1
                    # Scan past the next string content (handle escapes)
                    while k < len(text):
                        if text[k] == '\\' and k + 1 < len(text):
                            k += 2  # Skip escape sequence
                            continue
                        if text[k] == '"':
                            break  # Found closing quote
                        k += 1
                    # k now points to closing quote of next string (or end of text)
                    if k < len(text) and text[k] == '"':
                        # Found the closing quote - check what comes after
                        # Special case: if k == j + 1, the "next string" is empty ("")
                        # An empty string immediately following a value without comma
                        # is likely unescaped empty quotes, not a separate value
                        # e.g., '{"text": "The value is """}' - the "" should be in the string
                        if k == j + 1:
                            # Empty "next string" - treat as unescaped empty quotes
                            # Fall through to escape the current quote
                            pass
                        else:
                            m = k + 1
                            while m < len(text) and text[m] in ' \t\n\r':
                                m += 1
                            if m < len(text) and text[m] == ':':
                                # Next thing is a key, so current quote is closing
                                in_string = False
                                result.append(char)
                                i += 1
                                continue
                            if m < len(text) and text[m] in '},]':
                                # Next string is a value (end of object/array after it)
                                in_string = False
                                result.append(char)
                                i += 1
                                continue
                            if m < len(text) and text[m] == ',':
                                # Next string is followed by comma - could be value in array/object
                                # Check if we're in an object context (key-value pattern)
                                # Look back to see if there's a '{' before our string
                                in_object = False
                                for prev_char in reversed(result):
                                    if prev_char == '{':
                                        in_object = True
                                        break
                                    if prev_char == '[':
                                        break
                                if in_object:
                                    # In object: "key" "value", - this is key-value with missing colon
                                    in_string = False
                                    result.append(char)
                                    i += 1
                                    continue
                            # Check if next char is another quote (more strings in sequence)
                            if m < len(text) and text[m] == '"':
                                # Multiple strings in sequence - check array context
                                in_array = False
                                for prev_char in reversed(result):
                                    if prev_char == '[':
                                        in_array = True
                                        break
                                    if prev_char == '{':
                                        break
                                if in_array:
                                    # In array: ["a" "b" "c"] - these are separate strings
                                    in_string = False
                                    result.append(char)
                                    i += 1
                                    continue

                # Check if next char starts a non-string value (number, bool, null, {, [)
                # In object/array context, this is likely a key-value or array element
                is_value_start = (
                    next_char.isdigit() or
                    next_char == '-' or
                    next_char in '{[' or
                    text[j:].startswith(('true', 'false', 'null'))
                )
                if is_value_start:
                    # Special case: if it's a number followed by quote (like "2.0"),
                    # it might be a quoted phrase inside the string, not a separate value
                    # Check for pattern: "number" (number followed by closing quote)
                    if next_char.isdigit() or next_char == '-':
                        # Scan past the number
                        num_end = j
                        while num_end < len(text) and (text[num_end].isdigit() or
                                                        text[num_end] in '.-+eE'):
                            num_end += 1
                        # Check if number is immediately followed by a quote
                        if num_end < len(text) and text[num_end] == '"':
                            # Pattern like "2.0" - this is likely a quoted phrase
                            # Check what's after the closing quote
                            after_quote = num_end + 1
                            while after_quote < len(text) and text[after_quote] in ' \t':
                                after_quote += 1
                            # If followed by more text (not }, ], or ,), it's quoted phrase
                            if after_quote < len(text) and text[after_quote].isalnum():
                                # "number" followed by text - this is unescaped quote
                                # Fall through to escape
                                pass
                            else:
                                # Could be a quoted phrase at end, still escape
                                pass
                        else:
                            # Number not followed by quote - might be separate value
                            # Look back to see if we're in an object or array context
                            in_object = False
                            in_array = False
                            for prev_char in reversed(result):
                                if prev_char == '{':
                                    in_object = True
                                    break
                                if prev_char == '[':
                                    in_array = True
                                    break
                            if in_object or in_array:
                                # This is a key-value pair or array element with missing separator
                                in_string = False
                                result.append(char)
                                i += 1
                                continue
                    else:
                        # Not a number - check object/array context
                        in_object = False
                        in_array = False
                        for prev_char in reversed(result):
                            if prev_char == '{':
                                in_object = True
                                break
                            if prev_char == '[':
                                in_array = True
                                break
                        if in_object or in_array:
                            # This is a key-value pair or array element with missing separator
                            in_string = False
                            result.append(char)
                            i += 1
                            continue

                # Check if this is an unescaped internal quote
                # Look ahead for a pattern like: "word" followed by more text then "
                # This is an unescaped quote - escape it
                if repair_log is not None:
                    repair = create_repair(
                        kind=RepairKind.UNESCAPED_QUOTE,
                        text=text,
                        position=i,
                        original='"',
                        replacement='\\"',
                    )
                    repair_log.append(repair)

                result.append('\\')
                result.append('"')
                i += 1
                continue

        result.append(char)
        i += 1

    return "".join(result)


def remove_double_commas(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Remove double/empty commas from JSON.

    Handles patterns like:
    - {"a": 1,, "b": 2} → {"a": 1, "b": 2}
    - [1,, 2] → [1, 2]
    - {, "a": 1} → {"a": 1}
    - [, 1, 2] → [1, 2]

    Args:
        text: JSON text with possible double commas
        repair_log: Optional list to append Repair objects to

    Returns:
        Text with double commas removed
    """
    if not text:
        return text

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

        if char == '\\' and in_string:
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

        # Handle commas outside of strings
        if char == ',' and not in_string:
            # Check if this is a leading comma after { or [
            # Look back through result to find last non-whitespace
            last_structural = None
            for prev_char in reversed(result):
                if prev_char not in ' \t\n\r':
                    last_structural = prev_char
                    break

            if last_structural is not None and last_structural in '{[':
                # Leading comma - skip it
                if repair_log is not None:
                    repair = create_repair(
                        kind=RepairKind.DOUBLE_COMMA,
                        text=text,
                        position=i,
                        original=',',
                        replacement='',
                    )
                    repair_log.append(repair)
                i += 1
                continue

            if last_structural == ',':
                # Double comma - skip this one
                if repair_log is not None:
                    repair = create_repair(
                        kind=RepairKind.DOUBLE_COMMA,
                        text=text,
                        position=i,
                        original=',',
                        replacement='',
                    )
                    repair_log.append(repair)
                i += 1
                continue

        result.append(char)
        i += 1

    return "".join(result)


def convert_javascript_values(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Convert JavaScript values to JSON equivalents.

    Converts:
    - NaN → null
    - Infinity → null
    - -Infinity → null
    - +Infinity → null
    - undefined → null

    Args:
        text: JSON text with possible JavaScript values
        repair_log: Optional list to append Repair objects to

    Returns:
        Text with JavaScript values converted to null
    """
    if not text:
        return text

    result: list[str] = []
    i = 0
    in_string = False
    escape_next = False

    # JavaScript values to convert (case-sensitive)
    js_values = {
        'NaN': 'null',
        'Infinity': 'null',
        'undefined': 'null',
    }

    while i < len(text):
        char = text[i]

        # Handle escape sequences in strings
        if escape_next:
            result.append(char)
            escape_next = False
            i += 1
            continue

        if char == '\\' and in_string:
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

        # Check for JavaScript values outside strings
        if not in_string:
            # Check for -Infinity or +Infinity
            if char in '-+' and text[i:].startswith(f'{char}Infinity'):
                # Verify it's not part of another word
                end_pos = i + len(char) + len('Infinity')
                if end_pos >= len(text) or not text[end_pos].isalnum():
                    original = f'{char}Infinity'
                    if repair_log is not None:
                        repair = create_repair(
                            kind=RepairKind.JAVASCRIPT_VALUE,
                            text=text,
                            position=i,
                            original=original,
                            replacement='null',
                        )
                        repair_log.append(repair)
                    result.append('null')
                    i += len(original)
                    continue

            # Check for other JS values
            for js_val, replacement in js_values.items():
                if text[i:].startswith(js_val):
                    # Verify it's not part of another word
                    end_pos = i + len(js_val)
                    start_ok = (i == 0 or not text[i - 1].isalnum())
                    end_ok = (end_pos >= len(text) or not text[end_pos].isalnum())
                    if start_ok and end_ok:
                        if repair_log is not None:
                            repair = create_repair(
                                kind=RepairKind.JAVASCRIPT_VALUE,
                                text=text,
                                position=i,
                                original=js_val,
                                replacement=replacement,
                            )
                            repair_log.append(repair)
                        result.append(replacement)
                        i += len(js_val)
                        break
            else:
                # No match - append character
                result.append(char)
                i += 1
                continue
            continue

        result.append(char)
        i += 1

    return "".join(result)


def convert_number_formats(
    text: str,
    repair_log: list[Repair] | None = None,
) -> str:
    """Convert non-decimal number formats to decimal.

    Converts:
    - Hexadecimal: 0xFF → 255
    - Octal: 0o777 → 511
    - Binary: 0b1010 → 10

    Args:
        text: JSON text with possible non-decimal numbers
        repair_log: Optional list to append Repair objects to

    Returns:
        Text with numbers converted to decimal
    """
    if not text:
        return text

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

        if char == '\\' and in_string:
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

        # Check for number formats outside strings
        if not in_string:
            # Check for negative numbers
            negative = False
            start_i = i
            if char == '-' and i + 1 < len(text) and text[i + 1] == '0':
                negative = True
                i += 1
                char = text[i]

            if char == '0' and i + 1 < len(text):
                next_char = text[i + 1].lower()

                # Hexadecimal: 0x or 0X
                if next_char == 'x':
                    j = i + 2
                    while j < len(text) and text[j] in '0123456789abcdefABCDEF':
                        j += 1
                    if j > i + 2:  # Found at least one hex digit
                        hex_str = text[i:j]
                        try:
                            value = int(hex_str, 16)
                            if negative:
                                value = -value
                            original = text[start_i:j]
                            replacement = str(value)
                            if repair_log is not None:
                                repair = create_repair(
                                    kind=RepairKind.NUMBER_FORMAT,
                                    text=text,
                                    position=start_i,
                                    original=original,
                                    replacement=replacement,
                                )
                                repair_log.append(repair)
                            result.append(replacement)
                            i = j
                            continue
                        except ValueError:
                            pass

                # Octal: 0o or 0O
                elif next_char == 'o':
                    j = i + 2
                    while j < len(text) and text[j] in '01234567':
                        j += 1
                    if j > i + 2:  # Found at least one octal digit
                        oct_str = text[i:j]
                        try:
                            value = int(oct_str, 8)
                            if negative:
                                value = -value
                            original = text[start_i:j]
                            replacement = str(value)
                            if repair_log is not None:
                                repair = create_repair(
                                    kind=RepairKind.NUMBER_FORMAT,
                                    text=text,
                                    position=start_i,
                                    original=original,
                                    replacement=replacement,
                                )
                                repair_log.append(repair)
                            result.append(replacement)
                            i = j
                            continue
                        except ValueError:
                            pass

                # Binary: 0b or 0B
                elif next_char == 'b':
                    j = i + 2
                    while j < len(text) and text[j] in '01':
                        j += 1
                    if j > i + 2:  # Found at least one binary digit
                        bin_str = text[i:j]
                        try:
                            value = int(bin_str, 2)
                            if negative:
                                value = -value
                            original = text[start_i:j]
                            replacement = str(value)
                            if repair_log is not None:
                                repair = create_repair(
                                    kind=RepairKind.NUMBER_FORMAT,
                                    text=text,
                                    position=start_i,
                                    original=original,
                                    replacement=replacement,
                                )
                                repair_log.append(repair)
                            result.append(replacement)
                            i = j
                            continue
                        except ValueError:
                            pass

            # If we moved i for negative but didn't convert, reset
            if negative:
                result.append('-')

        result.append(char)
        i += 1

    return "".join(result)
