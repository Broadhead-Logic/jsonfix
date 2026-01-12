"""Tests for V2: Auto-close brackets."""

from __future__ import annotations

import json

import pytest

from jsonfix import loads_relaxed, RepairKind


class TestBasicAutoClose:
    """Test basic auto-close brackets."""

    def test_missing_object_close(self, repair_log: list) -> None:
        """Missing closing brace is added."""
        result = loads_relaxed('{"a": 1', repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1
        assert repair_log[0].kind == RepairKind.MISSING_BRACKET

    def test_missing_array_close(self, repair_log: list) -> None:
        """Missing closing bracket is added."""
        result = loads_relaxed("[1, 2, 3", repair_log=repair_log)
        assert result == [1, 2, 3]
        assert len(repair_log) == 1


class TestMultipleMissingBrackets:
    """Test multiple missing brackets."""

    def test_nested_missing_both(self, repair_log: list) -> None:
        """Missing closing for both nested brackets."""
        result = loads_relaxed('{"a": [1, 2', repair_log=repair_log)
        assert result == {"a": [1, 2]}
        assert len(repair_log) == 2  # ] and }

    def test_deeply_nested(self, repair_log: list) -> None:
        """Deeply nested missing brackets."""
        result = loads_relaxed('{"a": {"b": {"c": 1', repair_log=repair_log)
        assert result == {"a": {"b": {"c": 1}}}
        assert len(repair_log) == 3  # Three closing braces


class TestAlreadyComplete:
    """Test already complete JSON."""

    def test_complete_object_no_repair(self, repair_log: list) -> None:
        """Complete object needs no repair."""
        result = loads_relaxed('{"a": 1}', repair_log=repair_log)
        assert result == {"a": 1}
        # No MISSING_BRACKET repairs (may have other repairs like trailing comma)
        bracket_repairs = [r for r in repair_log if r.kind == RepairKind.MISSING_BRACKET]
        assert len(bracket_repairs) == 0

    def test_complete_array_no_repair(self, repair_log: list) -> None:
        """Complete array needs no repair."""
        result = loads_relaxed("[1, 2, 3]", repair_log=repair_log)
        assert result == [1, 2, 3]
        bracket_repairs = [r for r in repair_log if r.kind == RepairKind.MISSING_BRACKET]
        assert len(bracket_repairs) == 0


class TestWithOtherFeatures:
    """Test auto-close with other V2 features."""

    def test_auto_close_with_trailing_comma(self, repair_log: list) -> None:
        """Auto-close works with trailing comma."""
        result = loads_relaxed('{"a": 1,', repair_log=repair_log)
        assert result == {"a": 1}
        # Both trailing comma and missing bracket repairs

    def test_auto_close_with_single_quotes(self, repair_log: list) -> None:
        """Auto-close works with single-quoted strings."""
        result = loads_relaxed("{'a': 1", repair_log=repair_log)
        assert result == {"a": 1}

    def test_auto_close_with_unquoted_keys(self, repair_log: list) -> None:
        """Auto-close works with unquoted keys."""
        result = loads_relaxed("{key: 1", repair_log=repair_log)
        assert result == {"key": 1}


class TestComplexStructures:
    """Test complex structures with missing brackets."""

    def test_array_of_objects_missing_close(self, repair_log: list) -> None:
        """Array of objects with missing bracket."""
        result = loads_relaxed('[{"a": 1}, {"b": 2}', repair_log=repair_log)
        assert result == [{"a": 1}, {"b": 2}]

    def test_mixed_nesting(self, repair_log: list) -> None:
        """Mixed nesting with missing brackets."""
        result = loads_relaxed('[1, {"x": [2, 3', repair_log=repair_log)
        assert result == [1, {"x": [2, 3]}]


class TestDisabledOption:
    """Test disabling auto-close brackets."""

    def test_disabled_raises_error(self) -> None:
        """Disabled option raises error on missing bracket."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": 1', auto_close_brackets=False)

    def test_disabled_allows_complete_json(self, repair_log: list) -> None:
        """Complete JSON works when auto-close disabled."""
        result = loads_relaxed(
            '{"a": 1}',
            auto_close_brackets=False,
            repair_log=repair_log,
        )
        assert result == {"a": 1}


class TestBracketOrder:
    """Test correct bracket closing order."""

    def test_closes_in_correct_order(self, repair_log: list) -> None:
        """Brackets closed in LIFO order."""
        result = loads_relaxed('[{"a": [1', repair_log=repair_log)
        assert result == [{"a": [1]}]
        # Should close ] first, then }, then ]

    def test_interleaved_brackets(self, repair_log: list) -> None:
        """Interleaved brackets closed correctly."""
        result = loads_relaxed('{"arr": [1, 2], "obj": {"x": 1', repair_log=repair_log)
        assert result == {"arr": [1, 2], "obj": {"x": 1}}


class TestRepairLog:
    """Test repair log for auto-close."""

    def test_repair_log_records_bracket(self, repair_log: list) -> None:
        """Repair log records bracket addition."""
        loads_relaxed('{"a": 1', repair_log=repair_log)
        repair = repair_log[0]
        assert repair.kind == RepairKind.MISSING_BRACKET
        assert repair.replacement == "}"

    def test_repair_log_position_at_end(self, repair_log: list) -> None:
        """Repair position is at end of input."""
        json_str = '{"a": 1'
        loads_relaxed(json_str, repair_log=repair_log)
        repair = repair_log[0]
        assert repair.position == len(json_str)
