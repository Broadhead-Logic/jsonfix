"""Tests for valid JSON passthrough - ensure valid JSON passes unchanged."""

from __future__ import annotations

import pytest

from jsonfix import loads_relaxed


class TestBasicTypes:
    """Test basic JSON value types."""

    def test_empty_object(self, repair_log: list) -> None:
        """Empty object parses correctly."""
        result = loads_relaxed("{}", repair_log=repair_log)
        assert result == {}
        assert repair_log == []

    def test_empty_array(self, repair_log: list) -> None:
        """Empty array parses correctly."""
        result = loads_relaxed("[]", repair_log=repair_log)
        assert result == []
        assert repair_log == []

    def test_null(self, repair_log: list) -> None:
        """null parses to None."""
        result = loads_relaxed("null", repair_log=repair_log)
        assert result is None
        assert repair_log == []

    def test_boolean_true(self, repair_log: list) -> None:
        """true parses to True."""
        result = loads_relaxed("true", repair_log=repair_log)
        assert result is True
        assert repair_log == []

    def test_boolean_false(self, repair_log: list) -> None:
        """false parses to False."""
        result = loads_relaxed("false", repair_log=repair_log)
        assert result is False
        assert repair_log == []

    def test_integer(self, repair_log: list) -> None:
        """Integer parses correctly."""
        result = loads_relaxed("42", repair_log=repair_log)
        assert result == 42
        assert repair_log == []

    def test_negative_integer(self, repair_log: list) -> None:
        """Negative integer parses correctly."""
        result = loads_relaxed("-42", repair_log=repair_log)
        assert result == -42
        assert repair_log == []

    def test_float(self, repair_log: list) -> None:
        """Float parses correctly."""
        result = loads_relaxed("3.14", repair_log=repair_log)
        assert result == 3.14
        assert repair_log == []

    def test_scientific_notation(self, repair_log: list) -> None:
        """Scientific notation parses correctly."""
        result = loads_relaxed("1.5e10", repair_log=repair_log)
        assert result == 1.5e10
        assert repair_log == []

    def test_string(self, repair_log: list) -> None:
        """String parses correctly."""
        result = loads_relaxed('"hello"', repair_log=repair_log)
        assert result == "hello"
        assert repair_log == []

    def test_string_with_escapes(self, repair_log: list) -> None:
        """String with escape sequences parses correctly."""
        result = loads_relaxed('"hello\\nworld"', repair_log=repair_log)
        assert result == "hello\nworld"
        assert repair_log == []

    def test_string_with_unicode(self, repair_log: list) -> None:
        """String with unicode escape parses correctly."""
        result = loads_relaxed('"caf\\u00e9"', repair_log=repair_log)
        assert result == "café"
        assert repair_log == []


class TestComplexStructures:
    """Test complex JSON structures."""

    def test_simple_object(self, repair_log: list) -> None:
        """Simple object with multiple keys."""
        result = loads_relaxed('{"a": 1, "b": 2}', repair_log=repair_log)
        assert result == {"a": 1, "b": 2}
        assert repair_log == []

    def test_nested_object(self, repair_log: list) -> None:
        """Nested objects parse correctly."""
        result = loads_relaxed('{"a": {"b": {"c": 1}}}', repair_log=repair_log)
        assert result == {"a": {"b": {"c": 1}}}
        assert repair_log == []

    def test_simple_array(self, repair_log: list) -> None:
        """Simple array with multiple elements."""
        result = loads_relaxed("[1, 2, 3]", repair_log=repair_log)
        assert result == [1, 2, 3]
        assert repair_log == []

    def test_nested_array(self, repair_log: list) -> None:
        """Nested arrays parse correctly."""
        result = loads_relaxed("[[1, 2], [3, 4]]", repair_log=repair_log)
        assert result == [[1, 2], [3, 4]]
        assert repair_log == []

    def test_mixed_structure(self, repair_log: list) -> None:
        """Mixed objects and arrays."""
        result = loads_relaxed('{"a": [1, {"b": 2}]}', repair_log=repair_log)
        assert result == {"a": [1, {"b": 2}]}
        assert repair_log == []

    def test_complex_real_world(self, repair_log: list) -> None:
        """Complex nested structure like real-world JSON."""
        json_str = """
        {
            "users": [
                {"id": 1, "name": "Alice", "active": true},
                {"id": 2, "name": "Bob", "active": false}
            ],
            "metadata": {
                "total": 2,
                "page": 1,
                "per_page": 10
            }
        }
        """
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["users"][0]["name"] == "Alice"
        assert result["metadata"]["total"] == 2
        assert repair_log == []


class TestEdgeCases:
    """Test edge cases for valid JSON."""

    def test_empty_string(self, repair_log: list) -> None:
        """Empty string value parses correctly."""
        result = loads_relaxed('""', repair_log=repair_log)
        assert result == ""
        assert repair_log == []

    def test_string_with_quotes(self, repair_log: list) -> None:
        """String containing escaped quotes."""
        result = loads_relaxed('"say \\"hello\\""', repair_log=repair_log)
        assert result == 'say "hello"'
        assert repair_log == []

    def test_whitespace_preserved_in_strings(self, repair_log: list) -> None:
        """Whitespace inside strings is preserved."""
        result = loads_relaxed('"a b  c"', repair_log=repair_log)
        assert result == "a b  c"
        assert repair_log == []

    def test_leading_trailing_whitespace(self, repair_log: list) -> None:
        """Leading/trailing whitespace outside JSON is ignored."""
        result = loads_relaxed('  {"a": 1}  ', repair_log=repair_log)
        assert result == {"a": 1}
        assert repair_log == []

    def test_newlines_between_elements(self, repair_log: list) -> None:
        """Newlines between elements work correctly."""
        json_str = '{\n"a": 1,\n"b": 2\n}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}
        assert repair_log == []

    def test_all_valid_samples(
        self, sample_valid_json: list[str], repair_log: list
    ) -> None:
        """All sample valid JSON strings parse with no repairs."""
        for json_str in sample_valid_json:
            repair_log.clear()
            loads_relaxed(json_str, repair_log=repair_log)
            assert repair_log == [], f"Unexpected repairs for: {json_str}"
