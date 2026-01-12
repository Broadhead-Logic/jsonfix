"""Tests for V2: Unquoted key handling."""

from __future__ import annotations

import json

import pytest

from jsonfix import loads_relaxed, RepairKind


class TestBasicUnquotedKeys:
    """Test basic unquoted key handling."""

    def test_simple_unquoted_key(self, repair_log: list) -> None:
        """Simple unquoted key."""
        result = loads_relaxed("{key: 1}", repair_log=repair_log)
        assert result == {"key": 1}
        assert len(repair_log) == 1
        assert repair_log[0].kind == RepairKind.UNQUOTED_KEY

    def test_multiple_unquoted_keys(self, repair_log: list) -> None:
        """Multiple unquoted keys."""
        result = loads_relaxed("{a: 1, b: 2, c: 3}", repair_log=repair_log)
        assert result == {"a": 1, "b": 2, "c": 3}
        assert len(repair_log) == 3

    def test_mixed_quoted_unquoted(self, repair_log: list) -> None:
        """Mixed quoted and unquoted keys."""
        result = loads_relaxed('{a: 1, "b": 2}', repair_log=repair_log)
        assert result == {"a": 1, "b": 2}
        assert len(repair_log) == 1  # Only the unquoted key


class TestKeyIdentifiers:
    """Test various identifier formats for keys."""

    def test_underscore_in_key(self, repair_log: list) -> None:
        """Key with underscore."""
        result = loads_relaxed("{my_key: 1}", repair_log=repair_log)
        assert result == {"my_key": 1}

    def test_dollar_in_key(self, repair_log: list) -> None:
        """Key with dollar sign."""
        result = loads_relaxed("{$key: 1}", repair_log=repair_log)
        assert result == {"$key": 1}

    def test_numeric_suffix(self, repair_log: list) -> None:
        """Key with numeric suffix."""
        result = loads_relaxed("{key1: 1, key2: 2}", repair_log=repair_log)
        assert result == {"key1": 1, "key2": 2}

    def test_leading_underscore(self, repair_log: list) -> None:
        """Key with leading underscore."""
        result = loads_relaxed("{_private: 1}", repair_log=repair_log)
        assert result == {"_private": 1}

    def test_camel_case_key(self, repair_log: list) -> None:
        """CamelCase key."""
        result = loads_relaxed("{myKeyName: 1}", repair_log=repair_log)
        assert result == {"myKeyName": 1}


class TestNestedUnquotedKeys:
    """Test unquoted keys in nested structures."""

    def test_nested_object_unquoted(self, repair_log: list) -> None:
        """Nested object with unquoted keys."""
        result = loads_relaxed("{outer: {inner: 1}}", repair_log=repair_log)
        assert result == {"outer": {"inner": 1}}
        assert len(repair_log) == 2

    def test_deeply_nested(self, repair_log: list) -> None:
        """Deeply nested with unquoted keys."""
        result = loads_relaxed("{a: {b: {c: 1}}}", repair_log=repair_log)
        assert result == {"a": {"b": {"c": 1}}}
        assert len(repair_log) == 3


class TestKeywordsAsKeys:
    """Test JSON keywords used as keys."""

    def test_true_as_key(self, repair_log: list) -> None:
        """true as unquoted key (gets quoted, not converted to boolean)."""
        # When 'true' appears as a key position, it should be quoted as "true"
        result = loads_relaxed('{true: 1}', repair_log=repair_log)
        assert result == {"true": 1}

    def test_false_as_key(self, repair_log: list) -> None:
        """false as unquoted key."""
        result = loads_relaxed('{false: 1}', repair_log=repair_log)
        assert result == {"false": 1}

    def test_null_as_key(self, repair_log: list) -> None:
        """null as unquoted key."""
        result = loads_relaxed('{null: 1}', repair_log=repair_log)
        assert result == {"null": 1}


class TestDisabledOption:
    """Test disabling unquoted key handling."""

    def test_disabled_raises_error(self) -> None:
        """Disabled option raises error."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed("{key: 1}", allow_unquoted_keys=False)

    def test_disabled_allows_other_features(self, repair_log: list) -> None:
        """Other features work when disabled."""
        result = loads_relaxed(
            '{"a": 1,}',
            allow_unquoted_keys=False,
            repair_log=repair_log,
        )
        assert result == {"a": 1}


class TestWithWhitespace:
    """Test unquoted keys with various whitespace."""

    def test_whitespace_before_colon(self, repair_log: list) -> None:
        """Whitespace between key and colon."""
        result = loads_relaxed("{key : 1}", repair_log=repair_log)
        assert result == {"key": 1}

    def test_newline_before_key(self, repair_log: list) -> None:
        """Newline before unquoted key."""
        result = loads_relaxed("{\n  key: 1\n}", repair_log=repair_log)
        assert result == {"key": 1}


class TestRepairLog:
    """Test repair log for unquoted keys."""

    def test_repair_log_position(self, repair_log: list) -> None:
        """Repair log records correct position."""
        loads_relaxed("{key: 1}", repair_log=repair_log)
        repair = repair_log[0]
        assert repair.position == 1  # Position after {
        assert repair.original == "key"
        assert repair.replacement == '"key"'

    def test_repair_kind(self, repair_log: list) -> None:
        """Repair kind is UNQUOTED_KEY."""
        loads_relaxed("{key: 1}", repair_log=repair_log)
        assert repair_log[0].kind == RepairKind.UNQUOTED_KEY
