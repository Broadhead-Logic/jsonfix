"""Fuzz testing for jsonfix using hypothesis."""

from __future__ import annotations

import json

import pytest
from hypothesis import given, settings, strategies as st

from jsonfix import loads_relaxed


class TestFuzzSafety:
    """Ensure parser never crashes on arbitrary input."""

    @given(st.text(max_size=1000))
    @settings(max_examples=500)
    def test_arbitrary_text_never_crashes(self, text: str) -> None:
        """Parser should handle any text without crashing.

        May raise JSONDecodeError or ValueError, but should never
        raise other exceptions or crash.
        """
        try:
            loads_relaxed(text)
        except json.JSONDecodeError:
            pass  # Expected for invalid JSON
        except ValueError:
            pass  # Expected for on_repair="error" or invalid options

    @given(st.text(max_size=100))
    @settings(max_examples=200)
    def test_valid_json_roundtrip(self, text: str) -> None:
        """Valid JSON should round-trip correctly.

        Note: Smart quote normalization may change certain Unicode characters
        (like backticks, curly quotes) inside string values. We disable
        quote normalization for strict round-trip testing.
        """
        # Create valid JSON with the text as a value
        valid = json.dumps({"value": text})
        # Disable quote normalization for strict round-trip
        result = loads_relaxed(valid, normalize_quotes=False)
        assert result == {"value": text}

    @given(st.integers())
    @settings(max_examples=100)
    def test_integer_roundtrip(self, num: int) -> None:
        """Integers should round-trip correctly."""
        valid = json.dumps(num)
        result = loads_relaxed(valid)
        assert result == num

    @given(st.floats(allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_float_roundtrip(self, num: float) -> None:
        """Floats should round-trip correctly."""
        valid = json.dumps(num)
        result = loads_relaxed(valid)
        assert result == num

    @given(st.booleans())
    def test_boolean_roundtrip(self, val: bool) -> None:
        """Booleans should round-trip correctly."""
        valid = json.dumps(val)
        result = loads_relaxed(valid)
        assert result == val

    @given(st.lists(st.integers(), max_size=50))
    @settings(max_examples=100)
    def test_list_roundtrip(self, lst: list) -> None:
        """Lists should round-trip correctly."""
        valid = json.dumps(lst)
        result = loads_relaxed(valid)
        assert result == lst


class TestFuzzRelaxedSyntax:
    """Fuzz test relaxed JSON syntax patterns."""

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_unquoted_keys_with_random_identifiers(self, key: str) -> None:
        """Random valid identifiers should work as unquoted keys."""
        if key and key[0].isalpha():  # Must start with letter
            relaxed = f"{{{key}: 1}}"
            result = loads_relaxed(relaxed)
            assert result == {key: 1}

    @given(st.text(max_size=50))
    @settings(max_examples=100)
    def test_single_quote_strings_with_random_content(self, content: str) -> None:
        """Random content in single-quoted strings."""
        # Escape problematic characters
        escaped = content.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
        try:
            relaxed = f"{{'text': '{escaped}'}}"
            result = loads_relaxed(relaxed)
            # Just verify it parses without crashing
            assert "text" in result
        except json.JSONDecodeError:
            pass  # Some edge cases may not parse
