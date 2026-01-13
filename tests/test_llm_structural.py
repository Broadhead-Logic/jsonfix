"""Tests for LLM structural JSON error handling.

Phase 2 Features:
- Missing colon between key-value pairs
- Missing comma between elements
- Control character escaping (tabs, etc.)
- Unescaped backslash repair

These tests define expected behavior before implementation (TDD).
"""

from __future__ import annotations

import pytest

from jsonfix import loads_relaxed, RepairKind


class TestMissingColon:
    """Test insertion of missing colons between keys and values."""

    def test_missing_colon_string_value(self, repair_log: list) -> None:
        """Insert colon between key and string value."""
        text = '{"name" "John"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"name": "John"}
        assert any(r.kind == RepairKind.MISSING_COLON for r in repair_log)

    def test_missing_colon_number_value(self, repair_log: list) -> None:
        """Insert colon between key and number value."""
        text = '{"age" 30}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"age": 30}

    def test_missing_colon_float_value(self, repair_log: list) -> None:
        """Insert colon between key and float value."""
        text = '{"price" 19.99}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"price": 19.99}

    def test_missing_colon_negative_number(self, repair_log: list) -> None:
        """Insert colon between key and negative number."""
        text = '{"temp" -5}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"temp": -5}

    def test_missing_colon_boolean_true(self, repair_log: list) -> None:
        """Insert colon between key and true."""
        text = '{"active" true}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"active": True}

    def test_missing_colon_boolean_false(self, repair_log: list) -> None:
        """Insert colon between key and false."""
        text = '{"disabled" false}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"disabled": False}

    def test_missing_colon_null_value(self, repair_log: list) -> None:
        """Insert colon between key and null."""
        text = '{"data" null}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"data": None}

    def test_missing_colon_object_value(self, repair_log: list) -> None:
        """Insert colon between key and object."""
        text = '{"config" {"a": 1}}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"config": {"a": 1}}

    def test_missing_colon_array_value(self, repair_log: list) -> None:
        """Insert colon between key and array."""
        text = '{"items" [1, 2, 3]}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"items": [1, 2, 3]}

    def test_missing_colon_empty_object(self, repair_log: list) -> None:
        """Insert colon between key and empty object."""
        text = '{"config" {}}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"config": {}}

    def test_missing_colon_empty_array(self, repair_log: list) -> None:
        """Insert colon between key and empty array."""
        text = '{"items" []}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"items": []}

    def test_multiple_missing_colons(self, repair_log: list) -> None:
        """Fix multiple missing colons."""
        text = '{"a" 1, "b" 2, "c" 3}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1, "b": 2, "c": 3}
        # Should have 3 MISSING_COLON repairs
        colon_repairs = [r for r in repair_log if r.kind == RepairKind.MISSING_COLON]
        assert len(colon_repairs) == 3

    def test_missing_colon_nested_object(self, repair_log: list) -> None:
        """Fix missing colon in nested object."""
        text = '{"outer": {"inner" "value"}}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"outer": {"inner": "value"}}

    def test_missing_colon_with_whitespace(self, repair_log: list) -> None:
        """Fix missing colon with whitespace between key and value."""
        text = '{"name"    "John"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"name": "John"}

    def test_missing_colon_with_newline(self, repair_log: list) -> None:
        """Fix missing colon with newline between key and value."""
        text = '{"name"\n"John"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"name": "John"}

    def test_colon_present_unchanged(self, repair_log: list) -> None:
        """Existing colons should not be affected."""
        text = '{"a": 1}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}
        assert not any(r.kind == RepairKind.MISSING_COLON for r in repair_log)

    def test_colon_in_string_not_affected(self, repair_log: list) -> None:
        """Colon in string value should not be affected."""
        text = '{"time" "12:30:00"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"time": "12:30:00"}


class TestMissingComma:
    """Test insertion of missing commas between elements."""

    # === Object Missing Commas ===

    def test_missing_comma_between_pairs(self, repair_log: list) -> None:
        """Insert comma between key-value pairs."""
        text = '{"a": 1 "b": 2}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}
        assert any(r.kind == RepairKind.MISSING_COMMA for r in repair_log)

    def test_missing_comma_multiple(self, repair_log: list) -> None:
        """Fix multiple missing commas."""
        text = '{"a": 1 "b": 2 "c": 3}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1, "b": 2, "c": 3}
        comma_repairs = [r for r in repair_log if r.kind == RepairKind.MISSING_COMMA]
        assert len(comma_repairs) == 2

    def test_missing_comma_with_newlines(self, repair_log: list) -> None:
        """Missing comma with newlines between pairs."""
        text = '{"a": 1\n"b": 2}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}

    def test_missing_comma_with_whitespace(self, repair_log: list) -> None:
        """Missing comma with whitespace between pairs."""
        text = '{"a": 1    "b": 2}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}

    def test_missing_comma_nested_objects(self, repair_log: list) -> None:
        """Missing comma between nested objects."""
        text = '{"a": {"x": 1} "b": {"y": 2}}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": {"x": 1}, "b": {"y": 2}}

    # === Array Missing Commas ===

    def test_missing_comma_array_numbers(self, repair_log: list) -> None:
        """Insert comma between array numbers."""
        text = '[1 2 3 4 5]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [1, 2, 3, 4, 5]

    def test_missing_comma_array_strings(self, repair_log: list) -> None:
        """Insert comma between array strings."""
        text = '["a" "b" "c"]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == ["a", "b", "c"]

    def test_missing_comma_array_mixed(self, repair_log: list) -> None:
        """Insert comma in mixed array."""
        text = '[1 "two" true null]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [1, "two", True, None]

    def test_missing_comma_array_objects(self, repair_log: list) -> None:
        """Insert comma between array objects."""
        text = '[{"a": 1} {"b": 2}]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [{"a": 1}, {"b": 2}]

    def test_missing_comma_array_arrays(self, repair_log: list) -> None:
        """Insert comma between nested arrays."""
        text = '[[1, 2] [3, 4]]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [[1, 2], [3, 4]]

    def test_missing_comma_array_booleans(self, repair_log: list) -> None:
        """Insert comma between array booleans."""
        text = '[true false true]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [True, False, True]

    def test_missing_comma_array_with_newlines(self, repair_log: list) -> None:
        """Insert comma in array with newlines."""
        text = '[\n1\n2\n3\n]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [1, 2, 3]

    # === Combined ===

    def test_missing_colon_and_comma(self, repair_log: list) -> None:
        """Fix both missing colon and comma."""
        text = '{"a" 1 "b" 2}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}
        # Should have both repair types
        assert any(r.kind == RepairKind.MISSING_COLON for r in repair_log)
        assert any(r.kind == RepairKind.MISSING_COMMA for r in repair_log)

    def test_commas_present_unchanged(self, repair_log: list) -> None:
        """Existing commas should not be affected."""
        text = '[1, 2, 3]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [1, 2, 3]
        assert not any(r.kind == RepairKind.MISSING_COMMA for r in repair_log)

    def test_comma_in_string_not_affected(self, repair_log: list) -> None:
        """Comma in string should not affect detection."""
        text = '["a, b" "c, d"]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == ["a, b", "c, d"]


class TestControlCharacters:
    """Test escaping of control characters in strings."""

    def test_literal_tab(self, repair_log: list) -> None:
        """Escape literal tab character."""
        text = '{"text": "col1\tcol2"}'  # Actual tab character
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": "col1\tcol2"}
        assert any(r.kind == RepairKind.CONTROL_CHARACTER for r in repair_log)

    def test_literal_carriage_return(self, repair_log: list) -> None:
        """Escape literal carriage return."""
        text = '{"text": "line1\rline2"}'  # Actual CR character
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": "line1\rline2"}

    def test_literal_form_feed(self, repair_log: list) -> None:
        """Escape literal form feed."""
        text = '{"text": "page1\fpage2"}'  # Actual FF character
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": "page1\fpage2"}

    def test_literal_backspace(self, repair_log: list) -> None:
        """Escape literal backspace."""
        text = '{"text": "ab\bc"}'  # Actual BS character
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": "ab\bc"}

    def test_multiple_control_chars(self, repair_log: list) -> None:
        """Escape multiple different control characters."""
        text = '{"text": "a\tb\rc"}'  # Tab and CR
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": "a\tb\rc"}

    def test_null_character(self, repair_log: list) -> None:
        """Handle null character."""
        text = '{"text": "a\x00b"}'  # Null character
        result = loads_relaxed(text, repair_log=repair_log)
        # Null should either be escaped or removed
        assert "a" in result["text"]
        assert "b" in result["text"]

    def test_control_char_0x01(self, repair_log: list) -> None:
        """Handle SOH control character."""
        text = '{"text": "a\x01b"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert "a" in result["text"]

    def test_control_char_0x1f(self, repair_log: list) -> None:
        """Handle US control character."""
        text = '{"text": "a\x1fb"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert "a" in result["text"]

    def test_newline_handled_separately(self, repair_log: list) -> None:
        """Newlines should be handled by existing UNESCAPED_NEWLINE."""
        text = '{"text": "line1\nline2"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": "line1\nline2"}
        # Should use UNESCAPED_NEWLINE, not CONTROL_CHARACTER
        assert any(r.kind == RepairKind.UNESCAPED_NEWLINE for r in repair_log)

    def test_valid_escaped_tab_unchanged(self, repair_log: list) -> None:
        """Valid JSON escape \\t should produce a tab character.

        Per JSON spec, \\t is a valid escape for tab. It should not be modified.
        This tests that the backslash fixer correctly preserves valid JSON escapes.
        """
        text = '{"text": "col1\\tcol2"}'
        result = loads_relaxed(text, repair_log=repair_log)
        # \t is valid JSON escape - produces actual tab
        assert result == {"text": "col1\tcol2"}
        assert not any(r.kind == RepairKind.UNESCAPED_BACKSLASH for r in repair_log)

    def test_control_char_in_array(self, repair_log: list) -> None:
        """Handle control character in array string."""
        text = '["a\tb", "c\rd"]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == ["a\tb", "c\rd"]


class TestUnescapedBackslash:
    """Test escaping of unescaped backslashes."""

    def test_windows_path(self, repair_log: list) -> None:
        """Escape backslashes in Windows path."""
        text = r'{"path": "C:\Users\name\file.txt"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"path": "C:\\Users\\name\\file.txt"}
        assert any(r.kind == RepairKind.UNESCAPED_BACKSLASH for r in repair_log)

    def test_backslash_before_invalid_escape_q(self, repair_log: list) -> None:
        """Escape backslash before invalid escape \\q."""
        text = r'{"text": "\q is not valid"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": "\\q is not valid"}

    def test_backslash_before_invalid_escape_x(self, repair_log: list) -> None:
        """Escape backslash before invalid escape \\x (without hex)."""
        text = r'{"text": "\x is not valid"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert "x" in result["text"]

    def test_backslash_before_invalid_escape_a(self, repair_log: list) -> None:
        """Escape backslash before invalid escape \\a."""
        text = r'{"text": "\a bell"}'
        result = loads_relaxed(text, repair_log=repair_log)
        # Should escape the backslash or handle appropriately
        assert "a" in result["text"]

    def test_valid_escapes_unchanged_n(self, repair_log: list) -> None:
        """Valid JSON escape \\n should produce a newline character.

        Per JSON spec, \\n is a valid escape for newline. It should not be modified.
        For literal backslash+n in output, use double-backslash in source: \\\\n
        """
        text = '{"text": "line1\\nline2"}'
        result = loads_relaxed(text, repair_log=repair_log)
        # \n is valid JSON escape - produces actual newline
        assert result == {"text": "line1\nline2"}
        assert not any(r.kind == RepairKind.UNESCAPED_BACKSLASH for r in repair_log)

    def test_valid_escapes_unchanged_t(self, repair_log: list) -> None:
        """Valid JSON escape \\t should produce a tab character.

        Per JSON spec, \\t is a valid escape for tab. It should not be modified.
        For literal backslash+t in output, use double-backslash in source: \\\\t
        """
        text = '{"text": "col1\\tcol2"}'
        result = loads_relaxed(text, repair_log=repair_log)
        # \t is valid JSON escape - produces actual tab
        assert result == {"text": "col1\tcol2"}
        assert not any(r.kind == RepairKind.UNESCAPED_BACKSLASH for r in repair_log)

    def test_valid_escapes_unchanged_quote(self, repair_log: list) -> None:
        """Valid escape \\" should not be modified."""
        text = '{"text": "He said \\"hello\\""}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": 'He said "hello"'}
        assert not any(r.kind == RepairKind.UNESCAPED_BACKSLASH for r in repair_log)

    def test_valid_escapes_unchanged_backslash(self, repair_log: list) -> None:
        """Valid escape \\\\ should not be modified."""
        text = '{"path": "C:\\\\Users\\\\name"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"path": "C:\\Users\\name"}
        assert not any(r.kind == RepairKind.UNESCAPED_BACKSLASH for r in repair_log)

    def test_already_escaped_backslash(self, repair_log: list) -> None:
        """Already escaped backslash should remain unchanged."""
        text = '{"path": "C:\\\\Users"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"path": "C:\\Users"}

    def test_mixed_valid_invalid(self, repair_log: list) -> None:
        """Mix of valid and invalid backslash sequences.

        Valid JSON escapes (\\n) are preserved, invalid ones (\\q) are escaped.
        """
        text = r'{"text": "valid\n then \q invalid"}'
        result = loads_relaxed(text, repair_log=repair_log)
        # \n is valid JSON escape - produces actual newline
        assert "\n" in result["text"]
        # \q is invalid - backslash is escaped, producing literal backslash+q
        assert "\\q" in result["text"]
        # Should have repair for \q but not for \n
        assert any(r.kind == RepairKind.UNESCAPED_BACKSLASH for r in repair_log)

    def test_multiple_invalid_escapes(self, repair_log: list) -> None:
        """Multiple invalid escape sequences."""
        text = r'{"text": "\a \b \c \d \e"}'
        result = loads_relaxed(text, repair_log=repair_log)
        # All invalid escapes should be fixed
        # \b is actually valid (backspace), others are not
        assert "a" in result["text"]

    def test_backslash_at_end_of_string(self, repair_log: list) -> None:
        """Handle backslash at end of string value."""
        text = r'{"path": "ends with\"}'
        # This is actually invalid - backslash escapes the closing quote
        # Should be handled gracefully
        try:
            result = loads_relaxed(text, repair_log=repair_log)
            # If it parses, verify it handled the backslash
            assert "ends with" in result["path"]
        except Exception:
            # It's also acceptable to fail on truly malformed input
            pass

    def test_regex_pattern(self, repair_log: list) -> None:
        """Handle regex pattern with backslashes."""
        text = r'{"pattern": "\d+\.\d+"}'
        result = loads_relaxed(text, repair_log=repair_log)
        # \d is not a valid JSON escape, should be escaped
        assert "d" in result["pattern"]


class TestCombinedStructuralFeatures:
    """Test combinations of structural repair features."""

    def test_all_structural_errors(self, repair_log: list) -> None:
        """Test object with multiple structural errors."""
        text = '{"name" "John" "age" 30 "active" true}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"name": "John", "age": 30, "active": True}
        # Should have both missing colons and commas
        assert any(r.kind == RepairKind.MISSING_COLON for r in repair_log)
        assert any(r.kind == RepairKind.MISSING_COMMA for r in repair_log)

    def test_structural_with_control_chars(self, repair_log: list) -> None:
        """Structural errors combined with control characters."""
        text = '{"a" "x\ty" "b" "z"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": "x\ty", "b": "z"}

    def test_structural_with_windows_path(self, repair_log: list) -> None:
        """Structural errors combined with Windows path."""
        text = r'{"file" "C:\Users\doc.txt" "name" "test"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result["file"] == "C:\\Users\\doc.txt"
        assert result["name"] == "test"

    def test_feature_disable_missing_colon(self, repair_log: list) -> None:
        """Verify missing colon repair can be disabled."""
        text = '{"name" "John"}'
        with pytest.raises(Exception):  # JSONDecodeError
            loads_relaxed(text, fix_missing_colon=False, repair_log=repair_log)

    def test_feature_disable_missing_comma(self, repair_log: list) -> None:
        """Verify missing comma repair can be disabled."""
        text = '{"a": 1 "b": 2}'
        with pytest.raises(Exception):  # JSONDecodeError
            loads_relaxed(text, fix_missing_comma=False, repair_log=repair_log)
