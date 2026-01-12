"""Tests for V2: Newline escaping in strings."""

from __future__ import annotations

import json

import pytest

from jsonfix import loads_relaxed, RepairKind


class TestBasicNewlineEscaping:
    """Test basic newline escaping."""

    def test_literal_newline(self, repair_log: list) -> None:
        """Literal newline in string is escaped."""
        json_str = '{"a": "line1\nline2"}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": "line1\nline2"}
        assert len(repair_log) == 1
        assert repair_log[0].kind == RepairKind.UNESCAPED_NEWLINE

    def test_literal_carriage_return(self, repair_log: list) -> None:
        """Literal carriage return in string is escaped."""
        json_str = '{"a": "line1\rline2"}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": "line1\rline2"}
        assert len(repair_log) == 1

    def test_crlf(self, repair_log: list) -> None:
        """CRLF in string is escaped."""
        json_str = '{"a": "line1\r\nline2"}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": "line1\r\nline2"}
        assert len(repair_log) == 2  # \r and \n each


class TestMultipleNewlines:
    """Test multiple newlines."""

    def test_multiple_newlines_in_string(self, repair_log: list) -> None:
        """Multiple newlines in one string."""
        json_str = '{"a": "line1\nline2\nline3"}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": "line1\nline2\nline3"}
        assert len(repair_log) == 2

    def test_newlines_in_multiple_strings(self, repair_log: list) -> None:
        """Newlines in multiple strings."""
        json_str = '{"a": "one\ntwo", "b": "three\nfour"}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["a"] == "one\ntwo"
        assert result["b"] == "three\nfour"


class TestAlreadyEscaped:
    """Test already escaped newlines."""

    def test_already_escaped_newline(self, repair_log: list) -> None:
        """Already escaped \\n passes through."""
        json_str = '{"a": "line1\\nline2"}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": "line1\nline2"}
        assert len(repair_log) == 0  # No repairs needed

    def test_already_escaped_cr(self, repair_log: list) -> None:
        """Already escaped \\r passes through."""
        json_str = '{"a": "line1\\rline2"}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": "line1\rline2"}
        assert len(repair_log) == 0


class TestNewlinesOutsideStrings:
    """Test newlines outside strings."""

    def test_newlines_between_elements(self, repair_log: list) -> None:
        """Newlines between JSON elements are preserved."""
        json_str = '{\n  "a": 1,\n  "b": 2\n}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}
        assert len(repair_log) == 0  # No repairs - newlines outside strings


class TestDisabledOption:
    """Test disabling newline escaping."""

    def test_disabled_causes_error(self) -> None:
        """Disabled option causes JSON error on literal newlines."""
        json_str = '{"a": "line1\nline2"}'
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed(json_str, escape_newlines=False)

    def test_disabled_allows_escaped(self, repair_log: list) -> None:
        """Already escaped newlines work when disabled."""
        json_str = '{"a": "line1\\nline2"}'
        result = loads_relaxed(
            json_str,
            escape_newlines=False,
            repair_log=repair_log,
        )
        assert result == {"a": "line1\nline2"}


class TestRepairLog:
    """Test repair log for newline escaping."""

    def test_repair_log_position(self, repair_log: list) -> None:
        """Repair log records position."""
        json_str = '{"a": "x\ny"}'
        loads_relaxed(json_str, repair_log=repair_log)
        repair = repair_log[0]
        assert repair.kind == RepairKind.UNESCAPED_NEWLINE
        assert "\\n" in repair.message or "newline" in repair.message.lower()
