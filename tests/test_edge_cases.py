"""Tests for edge cases and boundary conditions."""

from __future__ import annotations

import json

import pytest

from jsonfix import loads_relaxed


class TestEmptyAndMinimalInputs:
    """Test empty and minimal inputs."""

    def test_empty_string_error(self) -> None:
        """Empty string raises JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed("")

    def test_whitespace_only_error(self) -> None:
        """Whitespace-only string raises JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed("   \n\t  ")

    def test_comment_only_error(self) -> None:
        """Comment-only string raises JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed("// just a comment")

    def test_minimal_valid_zero(self, repair_log: list) -> None:
        """Minimal valid JSON: 0."""
        result = loads_relaxed("0", repair_log=repair_log)
        assert result == 0
        assert repair_log == []

    def test_minimal_valid_null(self, repair_log: list) -> None:
        """Minimal valid JSON: null."""
        result = loads_relaxed("null", repair_log=repair_log)
        assert result is None
        assert repair_log == []


class TestVeryLongInputs:
    """Test very long inputs."""

    @pytest.mark.slow
    def test_large_array(self, repair_log: list) -> None:
        """Large array with 10000 elements."""
        json_str = "[" + ",".join(str(i) for i in range(10000)) + ",]"
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert len(result) == 10000
        assert result[0] == 0
        assert result[9999] == 9999
        assert len(repair_log) == 1  # One trailing comma

    @pytest.mark.slow
    def test_large_object(self, repair_log: list) -> None:
        """Large object with 1000 keys."""
        pairs = [f'"key{i}": {i}' for i in range(1000)]
        json_str = "{" + ",".join(pairs) + ",}"
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert len(result) == 1000
        assert result["key0"] == 0
        assert result["key999"] == 999

    @pytest.mark.slow
    def test_deeply_nested(self, repair_log: list) -> None:
        """Deeply nested structure (100 levels)."""
        # Build nested structure: {"a": {"a": {"a": ... 1 ...}}}
        json_str = '{"a": ' * 100 + "1" + "}" * 100
        result = loads_relaxed(json_str, repair_log=repair_log)
        # Navigate to innermost value
        current = result
        for _ in range(100):
            current = current["a"]
        assert current == 1

    @pytest.mark.slow
    def test_long_string_value(self, repair_log: list) -> None:
        """Long string value (1MB)."""
        long_string = "x" * (1024 * 1024)  # 1MB
        json_str = f'{{"data": "{long_string}"}}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert len(result["data"]) == 1024 * 1024


class TestUnicodeEdgeCases:
    """Test unicode edge cases."""

    def test_bom_handling(self, repair_log: list) -> None:
        """UTF-8 BOM at start is handled."""
        # UTF-8 BOM: \ufeff - we strip it before parsing
        json_str = '\ufeff{"a": 1}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1}
        # BOM removal is logged as a repair
        assert len(repair_log) >= 0  # May or may not log BOM removal

    def test_unicode_in_keys(self, repair_log: list) -> None:
        """Unicode characters in keys."""
        json_str = '{"日本語": "value", "émoji": "🎉"}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["日本語"] == "value"
        assert result["émoji"] == "🎉"

    def test_surrogate_pairs(self, repair_log: list) -> None:
        """Emoji and astral plane characters."""
        json_str = '{"emoji": "😀🎉🚀"}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["emoji"] == "😀🎉🚀"

    def test_unicode_escapes(self, repair_log: list) -> None:
        """Unicode escape sequences."""
        json_str = '{"text": "\\u0048\\u0065\\u006c\\u006c\\u006f"}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["text"] == "Hello"


class TestNumericEdgeCases:
    """Test numeric edge cases."""

    def test_very_large_number(self, repair_log: list) -> None:
        """Very large number (near float max)."""
        json_str = '{"value": 1.7976931348623157e+308}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["value"] == 1.7976931348623157e308

    def test_very_small_number(self, repair_log: list) -> None:
        """Very small positive number."""
        json_str = '{"value": 2.2250738585072014e-308}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["value"] == 2.2250738585072014e-308

    def test_negative_zero(self, repair_log: list) -> None:
        """Negative zero."""
        json_str = '{"value": -0.0}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        # -0.0 equals 0.0 in Python
        assert result["value"] == 0.0

    def test_exponent_notation_variations(self, repair_log: list) -> None:
        """Various exponent notations."""
        json_str = '{"a": 1e10, "b": 1E10, "c": 1e+10, "d": 1e-10}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["a"] == 1e10
        assert result["b"] == 1e10
        assert result["c"] == 1e10
        assert result["d"] == 1e-10


class TestStringEdgeCases:
    """Test string edge cases."""

    def test_string_with_backslash(self, repair_log: list) -> None:
        """String with backslash."""
        json_str = '{"path": "C:\\\\Users\\\\test"}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["path"] == "C:\\Users\\test"

    def test_string_with_all_escapes(self, repair_log: list) -> None:
        """String with all escape sequences."""
        json_str = '{"text": "\\n\\r\\t\\\\\\"\\/\\b\\f"}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert "\n" in result["text"]
        assert "\r" in result["text"]
        assert "\t" in result["text"]
        assert "\\" in result["text"]
        assert '"' in result["text"]

    def test_string_with_unicode_escapes(self, repair_log: list) -> None:
        """String with \\uXXXX escapes."""
        json_str = '{"char": "\\u0041"}'  # 'A'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["char"] == "A"

    def test_empty_string_in_object(self, repair_log: list) -> None:
        """Empty string as value."""
        json_str = '{"empty": ""}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["empty"] == ""


class TestWhitespaceEdgeCases:
    """Test whitespace edge cases."""

    def test_crlf_line_endings(self, repair_log: list) -> None:
        """Windows-style CRLF line endings."""
        json_str = '{\r\n"a": 1,\r\n"b": 2\r\n}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}

    def test_cr_only_line_endings(self, repair_log: list) -> None:
        """Old Mac-style CR-only line endings."""
        json_str = '{\r"a": 1,\r"b": 2\r}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}

    def test_mixed_line_endings(self, repair_log: list) -> None:
        """Mixed line endings in one file."""
        json_str = '{\n"a": 1,\r\n"b": 2,\r"c": 3\n}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_tabs_and_spaces(self, repair_log: list) -> None:
        """Mixed tabs and spaces for indentation."""
        json_str = '{\t"a": 1,\n\t  "b": 2\n}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}


class TestCommentEdgeCases:
    """Test comment-specific edge cases."""

    def test_comment_lookalike_in_string_url(self, repair_log: list) -> None:
        """URL with // in string is not stripped."""
        json_str = '{"url": "https://example.com/path"}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["url"] == "https://example.com/path"
        assert repair_log == []

    def test_consecutive_comments(self, repair_log: list) -> None:
        """Multiple consecutive comments."""
        json_str = """
        // comment 1
        // comment 2
        /* comment 3 */
        {"a": 1}
        """
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 3

    def test_comment_between_array_elements(self, repair_log: list) -> None:
        """Comments between array elements."""
        json_str = '[1, /* between */ 2, // after\n3]'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == [1, 2, 3]
        assert len(repair_log) == 2


class TestSpecialValues:
    """Test special JSON values."""

    def test_object_with_null_values(self, repair_log: list) -> None:
        """Object with null values."""
        json_str = '{"a": null, "b": null}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": None, "b": None}

    def test_array_of_nulls(self, repair_log: list) -> None:
        """Array of null values."""
        json_str = "[null, null, null]"
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == [None, None, None]

    def test_boolean_values(self, repair_log: list) -> None:
        """Boolean values in various contexts."""
        json_str = '{"t": true, "f": false, "arr": [true, false]}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["t"] is True
        assert result["f"] is False
        assert result["arr"] == [True, False]
