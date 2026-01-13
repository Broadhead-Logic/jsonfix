"""Tests for trailing comma handling."""

from __future__ import annotations

import json

import pytest

from jsonfix import loads_relaxed, RepairKind


class TestObjectTrailingCommas:
    """Test trailing commas in objects."""

    def test_single_trailing_comma_object(self, repair_log: list) -> None:
        """Single trailing comma in object."""
        result = loads_relaxed('{"a": 1,}', repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1
        assert repair_log[0].kind == RepairKind.TRAILING_COMMA

    def test_trailing_comma_multiple_keys(self, repair_log: list) -> None:
        """Trailing comma with multiple keys."""
        result = loads_relaxed('{"a": 1, "b": 2,}', repair_log=repair_log)
        assert result == {"a": 1, "b": 2}
        assert len(repair_log) == 1

    def test_nested_object_trailing(self, repair_log: list) -> None:
        """Nested objects with trailing commas."""
        result = loads_relaxed('{"a": {"b": 1,},}', repair_log=repair_log)
        assert result == {"a": {"b": 1}}
        assert len(repair_log) == 2  # Two trailing commas

    def test_trailing_comma_with_whitespace(self, repair_log: list) -> None:
        """Trailing comma with extra whitespace."""
        result = loads_relaxed('{"a": 1 , }', repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1

    def test_trailing_comma_with_newline(self, repair_log: list) -> None:
        """Trailing comma with newline before closing brace."""
        result = loads_relaxed('{"a": 1,\n}', repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1


class TestArrayTrailingCommas:
    """Test trailing commas in arrays."""

    def test_single_trailing_comma_array(self, repair_log: list) -> None:
        """Single trailing comma in array."""
        result = loads_relaxed("[1,]", repair_log=repair_log)
        assert result == [1]
        assert len(repair_log) == 1
        assert repair_log[0].kind == RepairKind.TRAILING_COMMA

    def test_trailing_comma_multiple_elements(self, repair_log: list) -> None:
        """Trailing comma with multiple elements."""
        result = loads_relaxed("[1, 2, 3,]", repair_log=repair_log)
        assert result == [1, 2, 3]
        assert len(repair_log) == 1

    def test_nested_array_trailing(self, repair_log: list) -> None:
        """Nested arrays with trailing commas."""
        result = loads_relaxed("[[1,], [2,],]", repair_log=repair_log)
        assert result == [[1], [2]]
        assert len(repair_log) == 3  # Three trailing commas

    def test_trailing_comma_mixed_types(self, repair_log: list) -> None:
        """Trailing comma with mixed element types."""
        result = loads_relaxed('["a", 1, true,]', repair_log=repair_log)
        assert result == ["a", 1, True]
        assert len(repair_log) == 1


class TestMultipleCommasError:
    """Test that multiple consecutive commas are errors when feature is disabled."""

    def test_multiple_commas_error_array(self) -> None:
        """Multiple commas in array should error when feature is disabled."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed("[1,,]", remove_double_commas=False)

    def test_multiple_commas_error_array_middle(self) -> None:
        """Multiple commas in middle of array should error when feature is disabled."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed("[1,, 2]", remove_double_commas=False)

    def test_multiple_commas_in_object(self) -> None:
        """Multiple commas in object should error when feature is disabled."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": 1,, "b": 2}', remove_double_commas=False)


class TestRepairLog:
    """Test repair log accuracy for trailing commas."""

    def test_repair_log_records_position(self, repair_log: list) -> None:
        """Repair log records correct position."""
        loads_relaxed('{"a": 1,}', repair_log=repair_log)
        repair = repair_log[0]
        assert repair.position == 7  # Position of the trailing comma
        assert repair.line == 1
        assert repair.column == 8

    def test_repair_log_kind_is_trailing_comma(self, repair_log: list) -> None:
        """Repair kind is TRAILING_COMMA."""
        loads_relaxed("[1,]", repair_log=repair_log)
        assert repair_log[0].kind == RepairKind.TRAILING_COMMA

    def test_multiple_repairs_logged(self, repair_log: list) -> None:
        """Multiple trailing commas are all logged."""
        loads_relaxed('{"a": [1,], "b": [2,],}', repair_log=repair_log)
        trailing_comma_repairs = [
            r for r in repair_log if r.kind == RepairKind.TRAILING_COMMA
        ]
        assert len(trailing_comma_repairs) == 3

    def test_repair_message_descriptive(self, repair_log: list) -> None:
        """Repair message is descriptive."""
        loads_relaxed('{"a": 1,}', repair_log=repair_log)
        assert "trailing comma" in repair_log[0].message.lower()


class TestStrictMode:
    """Test strict mode rejects trailing commas."""

    def test_strict_mode_rejects_trailing_comma_object(self) -> None:
        """Strict mode rejects trailing comma in object."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": 1,}', strict=True)

    def test_strict_mode_rejects_trailing_comma_array(self) -> None:
        """Strict mode rejects trailing comma in array."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed("[1,]", strict=True)

    def test_strict_mode_accepts_valid_json(self, repair_log: list) -> None:
        """Strict mode accepts valid JSON."""
        result = loads_relaxed('{"a": 1}', strict=True, repair_log=repair_log)
        assert result == {"a": 1}
        assert repair_log == []


class TestDisabledOption:
    """Test with allow_trailing_commas=False."""

    def test_disabled_rejects_trailing_comma(self) -> None:
        """Disabling trailing comma option causes error."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": 1,}', allow_trailing_commas=False)

    def test_disabled_allows_other_relaxations(self, repair_log: list) -> None:
        """Other relaxations still work when trailing comma is disabled."""
        result = loads_relaxed(
            '{"a": 1} // comment',
            allow_trailing_commas=False,
            repair_log=repair_log,
        )
        assert result == {"a": 1}
        assert len(repair_log) == 1  # Comment removal only
