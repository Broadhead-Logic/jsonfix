"""Tests for additional API functions and coverage."""

from __future__ import annotations

import io
import json

import pytest

from jsonfix import (
    can_parse,
    get_repairs,
    load_relaxed,
    loads_relaxed,
    Repair,
    RepairKind,
)
from jsonfix.normalizers import has_smart_quotes


class TestLoadRelaxed:
    """Test load_relaxed function (file-like object support)."""

    def test_load_from_stringio(self, repair_log: list) -> None:
        """Load from StringIO object."""
        fp = io.StringIO('{"a": 1,}')
        result = load_relaxed(fp, repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1

    def test_load_with_comments(self, repair_log: list) -> None:
        """Load JSON with comments from file-like object."""
        fp = io.StringIO('// comment\n{"a": 1}')
        result = load_relaxed(fp, repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1

    def test_load_valid_json(self, repair_log: list) -> None:
        """Load valid JSON from file-like object."""
        fp = io.StringIO('{"a": 1, "b": 2}')
        result = load_relaxed(fp, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}
        assert repair_log == []

    def test_load_strict_mode(self) -> None:
        """Strict mode works with file-like object."""
        fp = io.StringIO('{"a": 1}')
        result = load_relaxed(fp, strict=True)
        assert result == {"a": 1}

    def test_load_invalid_json_error(self) -> None:
        """Invalid JSON raises error."""
        fp = io.StringIO('{"a": }')
        with pytest.raises(json.JSONDecodeError):
            load_relaxed(fp)


class TestCanParse:
    """Test can_parse function."""

    def test_valid_json_can_parse(self) -> None:
        """Valid JSON returns True."""
        assert can_parse('{"a": 1}') is True

    def test_relaxed_json_can_parse(self) -> None:
        """Relaxed JSON with trailing comma returns True."""
        assert can_parse('{"a": 1,}') is True

    def test_relaxed_json_with_comments_can_parse(self) -> None:
        """Relaxed JSON with comments returns True."""
        assert can_parse('{"a": 1} // comment') is True

    def test_invalid_json_cannot_parse(self) -> None:
        """Invalid JSON returns False."""
        assert can_parse('{"a": }') is False

    def test_unclosed_object_can_parse_with_auto_close(self) -> None:
        """Unclosed object returns True with default auto_close_brackets."""
        # V2: auto_close_brackets is enabled by default
        assert can_parse('{"a": 1') is True

    def test_empty_string_cannot_parse(self) -> None:
        """Empty string returns False."""
        assert can_parse('') is False


class TestGetRepairs:
    """Test get_repairs function."""

    def test_get_repairs_valid_json(self) -> None:
        """Valid JSON has no repairs."""
        repairs = get_repairs('{"a": 1}')
        assert repairs == []

    def test_get_repairs_trailing_comma(self) -> None:
        """Get repairs for trailing comma."""
        repairs = get_repairs('{"a": 1,}')
        assert len(repairs) == 1
        assert repairs[0].kind == RepairKind.TRAILING_COMMA

    def test_get_repairs_multiple(self) -> None:
        """Get multiple repairs."""
        repairs = get_repairs('// comment\n{"a": 1,}')
        assert len(repairs) == 2

    def test_get_repairs_invalid_json(self) -> None:
        """Get repairs returns partial list for invalid JSON."""
        # Even if final parsing fails, we should get repairs collected
        repairs = get_repairs('// comment\n{"a": }')
        # Should have at least the comment repair
        assert len(repairs) >= 1

    def test_get_repairs_smart_quotes(
        self, smart_double_quotes: dict[str, str]
    ) -> None:
        """Get repairs for smart quotes."""
        left = smart_double_quotes["left"]
        right = smart_double_quotes["right"]
        repairs = get_repairs(f'{{{left}a{right}: 1}}')
        assert len(repairs) == 2
        assert all(r.kind == RepairKind.SMART_QUOTE for r in repairs)


class TestHasSmartQuotes:
    """Test has_smart_quotes utility function."""

    def test_has_smart_quotes_true(
        self, smart_double_quotes: dict[str, str]
    ) -> None:
        """Text with smart quotes returns True."""
        left = smart_double_quotes["left"]
        assert has_smart_quotes(f'hello {left}world{left}') is True

    def test_has_smart_quotes_false(self) -> None:
        """Text without smart quotes returns False."""
        assert has_smart_quotes('hello "world"') is False

    def test_has_smart_quotes_empty(self) -> None:
        """Empty string returns False."""
        assert has_smart_quotes('') is False

    def test_has_smart_quotes_single_quote(
        self, smart_single_quotes: dict[str, str]
    ) -> None:
        """Text with smart single quotes returns True."""
        right = smart_single_quotes["right"]
        assert has_smart_quotes(f"it{right}s fine") is True


class TestRepairCreationBranches:
    """Test Repair creation for full coverage."""

    def test_repair_kind_hash_comment_message(self, repair_log: list) -> None:
        """Hash comment repair has correct message."""
        loads_relaxed('{"a": 1} # comment', repair_log=repair_log)
        repair = repair_log[0]
        assert "hash comment" in repair.message.lower()

    def test_repair_long_comment_truncated(self, repair_log: list) -> None:
        """Long comment is truncated in message."""
        long_comment = "x" * 50
        loads_relaxed(f'// {long_comment}\n{{}}', repair_log=repair_log)
        repair = repair_log[0]
        assert "..." in repair.message

    def test_repair_short_comment_not_truncated(self, repair_log: list) -> None:
        """Short comment is not truncated."""
        loads_relaxed('// short\n{}', repair_log=repair_log)
        repair = repair_log[0]
        assert "short" in repair.message
        assert "..." not in repair.original


class TestNormalizersEmptyInput:
    """Test normalizers with empty input."""

    def test_normalize_empty_string(self) -> None:
        """Normalizing empty string returns empty string."""
        from jsonfix.normalizers import normalize_quotes

        result = normalize_quotes('')
        assert result == ''


class TestRepairPositionEdgeCases:
    """Test repair position calculation edge cases."""

    def test_position_at_end_of_text(self, repair_log: list) -> None:
        """Position calculation at end of text."""
        # Trailing comma right at the end
        loads_relaxed('[1,]', repair_log=repair_log)
        repair = repair_log[0]
        assert repair.position == 2

    def test_position_calculation_negative_guard(self) -> None:
        """Position calculation handles edge case of negative position."""
        from jsonfix.repairs import _calculate_line_column

        line, col = _calculate_line_column("hello", -5)
        assert line >= 1
        assert col >= 1

    def test_position_calculation_past_end(self) -> None:
        """Position calculation handles position past end of text."""
        from jsonfix.repairs import _calculate_line_column

        line, col = _calculate_line_column("hello", 100)
        assert line >= 1
        assert col >= 1
