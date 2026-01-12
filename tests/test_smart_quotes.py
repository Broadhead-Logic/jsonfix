"""Tests for smart quote normalization."""

from __future__ import annotations

import json

import pytest

from jsonfix import loads_relaxed, RepairKind


class TestSmartDoubleQuotes:
    """Test smart double quote normalization (Unicode U+201C, U+201D)."""

    def test_left_double_quote(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """Left smart double quote is normalized."""
        left = smart_double_quotes["left"]  # "
        # Use smart quote as the opening quote of the key
        json_str = f'{{{left}a": 1}}'  # {"a": 1} with smart opening quote
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1
        assert repair_log[0].kind == RepairKind.SMART_QUOTE

    def test_right_double_quote(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """Right smart double quote is normalized."""
        right = smart_double_quotes["right"]  # "
        # Use smart quote as the closing quote of the key
        json_str = f'{{"a{right}: 1}}'  # {"a": 1} with smart closing quote
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1

    def test_both_double_quotes(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """Both left and right smart quotes in key."""
        left = smart_double_quotes["left"]
        right = smart_double_quotes["right"]
        # Use both smart quotes as delimiters
        json_str = f'{{{left}a{right}: 1}}'  # {"a": 1} with both smart quotes
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 2  # Two quote replacements

    def test_smart_quotes_in_key_and_value(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """Smart quotes in both key and value."""
        left = smart_double_quotes["left"]
        right = smart_double_quotes["right"]
        json_str = f'{{{left}name{right}: {left}value{right}}}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"name": "value"}
        assert len(repair_log) == 4


class TestSmartSingleQuotes:
    """Test smart single quote normalization (Unicode U+2018, U+2019)."""

    def test_left_single_quote(
        self, repair_log: list, smart_single_quotes: dict[str, str]
    ) -> None:
        """Left smart single quote is normalized in string content."""
        left = smart_single_quotes["left"]  # '
        # Smart single quotes inside a string value
        json_str = f'{{"text": "it{left}s"}}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"text": "it's"}
        assert len(repair_log) == 1
        assert repair_log[0].kind == RepairKind.SMART_QUOTE

    def test_right_single_quote(
        self, repair_log: list, smart_single_quotes: dict[str, str]
    ) -> None:
        """Right smart single quote (apostrophe) is normalized."""
        right = smart_single_quotes["right"]  # '
        json_str = f'{{"text": "it{right}s"}}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"text": "it's"}
        assert len(repair_log) == 1

    def test_apostrophe_in_string(
        self, repair_log: list, smart_single_quotes: dict[str, str]
    ) -> None:
        """Smart apostrophe in string content."""
        right = smart_single_quotes["right"]
        json_str = f'{{"text": "don{right}t"}}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"text": "don't"}


class TestMixedQuoteScenarios:
    """Test mixed quote scenarios."""

    def test_mixed_smart_and_straight(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """Mix of smart and straight quotes."""
        left = smart_double_quotes["left"]
        # First key uses smart opening quote, second uses straight
        json_str = f'{{{left}a": 1, "b": 2}}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}
        assert len(repair_log) == 1  # Only one smart quote

    def test_smart_quotes_inside_string_value(
        self, repair_log: list, smart_single_quotes: dict[str, str]
    ) -> None:
        """Smart single quotes inside a string value are normalized."""
        # Use smart single quotes inside the string (these are safe to normalize)
        right = smart_single_quotes["right"]  # curly apostrophe
        json_str = f'{{"text": "she said it{right}s fine"}}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        # Smart apostrophe inside string is normalized to straight apostrophe
        assert result["text"] == "she said it's fine"
        assert len(repair_log) == 1

    def test_deeply_nested_smart_quotes(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """Smart quotes in deeply nested structure."""
        left = smart_double_quotes["left"]
        right = smart_double_quotes["right"]
        json_str = f'{{{left}a{right}: {{{left}b{right}: {{{left}c{right}: 1}}}}}}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": {"b": {"c": 1}}}
        assert len(repair_log) == 6  # 3 keys * 2 quotes each


class TestOtherUnicodeQuotes:
    """Test other Unicode quote variants."""

    def test_guillemet_as_delimiter(self, repair_log: list) -> None:
        """Guillemet « used as key delimiter is normalized."""
        # Use guillemet as opening quote for key
        json_str = '{\u00abkey\u00bb: "value"}'  # «key»: "value"
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"key": "value"}
        assert len(repair_log) == 2  # Two guillemets normalized

    def test_double_prime_as_delimiter(self, repair_log: list) -> None:
        """Double prime ″ used as delimiter is normalized to double quote."""
        # Double prime normalizes to double quote "
        json_str = '{\u2033key\u2033: "value"}'  # ″key″: "value"
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"key": "value"}
        assert len(repair_log) == 2  # Two double primes normalized

    def test_low_double_quote_as_delimiter(self, repair_log: list) -> None:
        """Low double quote „ used as delimiter is normalized."""
        # Low-9 double quote normalizes to double quote "
        json_str = '{\u201ekey\u201e: "value"}'  # „key„: "value"
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"key": "value"}


class TestQuotesUnchanged:
    """Test that straight quotes pass through unchanged."""

    def test_straight_quotes_unchanged(self, repair_log: list) -> None:
        """Standard straight quotes produce no repairs."""
        result = loads_relaxed('{"a": "hello"}', repair_log=repair_log)
        assert result == {"a": "hello"}
        assert repair_log == []

    def test_unicode_in_string_content(self, repair_log: list) -> None:
        """Unicode content in strings is preserved."""
        result = loads_relaxed('{"emoji": "🎉"}', repair_log=repair_log)
        assert result == {"emoji": "🎉"}
        assert repair_log == []


class TestRepairLog:
    """Test repair log accuracy for smart quotes."""

    def test_repair_log_shows_quote_position(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """Repair log shows exact position of smart quote."""
        left = smart_double_quotes["left"]
        # Smart quote is at position 1 (after the opening brace)
        json_str = f'{{{left}a": 1}}'
        loads_relaxed(json_str, repair_log=repair_log)
        repair = repair_log[0]
        assert repair.position == 1  # Position of the smart quote
        assert repair.line == 1
        assert repair.column == 2

    def test_repair_shows_original_quote(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """Repair shows which quote was replaced."""
        left = smart_double_quotes["left"]
        json_str = f'{{{left}a": 1}}'
        loads_relaxed(json_str, repair_log=repair_log)
        repair = repair_log[0]
        assert repair.original == left
        assert repair.replacement == '"'

    def test_multiple_quote_repairs(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """All quote replacements are logged."""
        left = smart_double_quotes["left"]
        right = smart_double_quotes["right"]
        json_str = f'{{{left}a{right}: {left}b{right}}}'
        loads_relaxed(json_str, repair_log=repair_log)
        quote_repairs = [r for r in repair_log if r.kind == RepairKind.SMART_QUOTE]
        assert len(quote_repairs) == 4


class TestStrictMode:
    """Test strict mode rejects smart quotes."""

    def test_strict_rejects_smart_quotes(
        self, smart_double_quotes: dict[str, str]
    ) -> None:
        """Strict mode rejects smart quotes."""
        left = smart_double_quotes["left"]
        json_str = f'{{{left}a": 1}}'
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed(json_str, strict=True)


class TestDisabledOption:
    """Test with normalize_quotes=False."""

    def test_disabled_rejects_smart_quotes(
        self, smart_double_quotes: dict[str, str]
    ) -> None:
        """Disabling quote normalization causes error on smart quotes."""
        left = smart_double_quotes["left"]
        json_str = f'{{{left}a": 1}}'
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed(json_str, normalize_quotes=False)

    def test_disabled_allows_other_relaxations(self, repair_log: list) -> None:
        """Other relaxations still work when quote normalization is disabled."""
        result = loads_relaxed(
            '{"a": 1,}',
            normalize_quotes=False,
            repair_log=repair_log,
        )
        assert result == {"a": 1}
        assert len(repair_log) == 1  # Trailing comma removal only
