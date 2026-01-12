"""Tests for V2: Single-quote string conversion."""

from __future__ import annotations

import json

import pytest

from jsonfix import loads_relaxed, RepairKind


class TestBasicSingleQuoteStrings:
    """Test basic single-quote string conversion."""

    def test_simple_single_quote_key(self, repair_log: list) -> None:
        """Single-quoted key is converted."""
        result = loads_relaxed("{'a': 1}", repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1
        assert repair_log[0].kind == RepairKind.SINGLE_QUOTE_STRING

    def test_simple_single_quote_value(self, repair_log: list) -> None:
        """Single-quoted value is converted."""
        result = loads_relaxed('{"a": \'hello\'}', repair_log=repair_log)
        assert result == {"a": "hello"}
        assert len(repair_log) == 1

    def test_both_key_and_value_single_quoted(self, repair_log: list) -> None:
        """Both key and value single-quoted."""
        result = loads_relaxed("{'key': 'value'}", repair_log=repair_log)
        assert result == {"key": "value"}
        assert len(repair_log) == 2

    def test_multiple_keys_single_quoted(self, repair_log: list) -> None:
        """Multiple single-quoted keys."""
        result = loads_relaxed("{'a': 1, 'b': 2}", repair_log=repair_log)
        assert result == {"a": 1, "b": 2}
        assert len(repair_log) == 2


class TestMixedQuoteStyles:
    """Test mixed single and double quotes."""

    def test_mixed_key_quotes(self, repair_log: list) -> None:
        """Mixed quote styles for keys."""
        result = loads_relaxed("{'a': 1, \"b\": 2}", repair_log=repair_log)
        assert result == {"a": 1, "b": 2}
        assert len(repair_log) == 1  # Only single-quoted key

    def test_mixed_value_quotes(self, repair_log: list) -> None:
        """Mixed quote styles for values."""
        result = loads_relaxed("{\"a\": 'hello', \"b\": \"world\"}", repair_log=repair_log)
        assert result == {"a": "hello", "b": "world"}
        assert len(repair_log) == 1


class TestNestedQuotes:
    """Test nested/escaped quotes."""

    def test_double_quotes_inside_single(self, repair_log: list) -> None:
        """Double quotes inside single-quoted string."""
        result = loads_relaxed("{'text': 'he said \"hi\"'}", repair_log=repair_log)
        assert result == {"text": 'he said "hi"'}

    def test_escaped_single_quote(self, repair_log: list) -> None:
        """Escaped single quote inside single-quoted string."""
        result = loads_relaxed("{'text': 'it\\'s fine'}", repair_log=repair_log)
        assert result == {"text": "it's fine"}

    def test_empty_single_quote_string(self, repair_log: list) -> None:
        """Empty single-quoted string."""
        result = loads_relaxed("{'empty': ''}", repair_log=repair_log)
        assert result == {"empty": ""}


class TestSingleQuoteArrays:
    """Test single quotes in arrays."""

    def test_array_with_single_quote_strings(self, repair_log: list) -> None:
        """Array of single-quoted strings."""
        result = loads_relaxed("['a', 'b', 'c']", repair_log=repair_log)
        assert result == ["a", "b", "c"]
        assert len(repair_log) == 3

    def test_mixed_array(self, repair_log: list) -> None:
        """Array with mixed quote styles."""
        result = loads_relaxed("['a', \"b\", 'c']", repair_log=repair_log)
        assert result == ["a", "b", "c"]
        assert len(repair_log) == 2


class TestUnicodeInSingleQuotes:
    """Test unicode in single-quoted strings."""

    def test_unicode_content(self, repair_log: list) -> None:
        """Unicode content in single-quoted string."""
        result = loads_relaxed("{'emoji': '🎉'}", repair_log=repair_log)
        assert result == {"emoji": "🎉"}

    def test_unicode_key(self, repair_log: list) -> None:
        """Unicode in single-quoted key."""
        result = loads_relaxed("{'日本語': 'value'}", repair_log=repair_log)
        assert result == {"日本語": "value"}


class TestDisabledOption:
    """Test disabling single-quote conversion."""

    def test_disabled_raises_error(self) -> None:
        """Disabled option raises error on single quotes."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed("{'a': 1}", allow_single_quote_strings=False)

    def test_disabled_allows_other_features(self, repair_log: list) -> None:
        """Other features work when single quotes disabled."""
        result = loads_relaxed(
            '{"a": 1,}',
            allow_single_quote_strings=False,
            repair_log=repair_log,
        )
        assert result == {"a": 1}


class TestRepairLog:
    """Test repair log for single-quote conversion."""

    def test_repair_log_position(self, repair_log: list) -> None:
        """Repair log records correct position."""
        loads_relaxed("{'a': 1}", repair_log=repair_log)
        repair = repair_log[0]
        # Position 1 = after the opening {
        assert repair.position == 1
        assert repair.line == 1
        assert repair.column == 2

    def test_repair_log_original_and_replacement(self, repair_log: list) -> None:
        """Repair log shows original and replacement."""
        loads_relaxed("{'a': 1}", repair_log=repair_log)
        repair = repair_log[0]
        assert repair.original == "'a'"
        assert repair.replacement == '"a"'


class TestEscapeSequencesInSingleQuotes:
    """Test escape sequences inside single-quoted strings."""

    def test_escaped_double_quote_inside_single(self, repair_log: list) -> None:
        """Escaped double quote inside single-quoted string."""
        # Covers normalizers.py lines 162-164
        result = loads_relaxed(r"{'text': 'say \"hi\"'}", repair_log=repair_log)
        assert result == {"text": 'say "hi"'}

    def test_escaped_backslash_n_inside_single(self, repair_log: list) -> None:
        """Escaped backslash-n inside single-quoted string."""
        # Covers normalizers.py lines 165-168
        result = loads_relaxed(r"{'text': 'line1\nline2'}", repair_log=repair_log)
        assert result == {"text": "line1\nline2"}

    def test_escaped_tab_inside_single(self, repair_log: list) -> None:
        """Escaped backslash-t inside single-quoted string."""
        result = loads_relaxed(r"{'text': 'col1\tcol2'}", repair_log=repair_log)
        assert result == {"text": "col1\tcol2"}

    def test_escaped_backslash_inside_single(self, repair_log: list) -> None:
        """Escaped backslash inside single-quoted string."""
        result = loads_relaxed(r"{'path': 'C:\\Users'}", repair_log=repair_log)
        assert result == {"path": "C:\\Users"}

    def test_unclosed_single_quote_causes_error(self) -> None:
        """Unclosed single quote causes JSON decode error."""
        # Covers normalizers.py lines 206-208
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed("{'text': 'unclosed")
