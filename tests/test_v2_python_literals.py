"""Tests for V2: Python literal conversion."""

from __future__ import annotations

import json

import pytest

from jsonfix import loads_relaxed, RepairKind


class TestBasicPythonLiterals:
    """Test basic Python literal conversion."""

    def test_python_true(self, repair_log: list) -> None:
        """Python True converted to JSON true."""
        result = loads_relaxed('{"a": True}', repair_log=repair_log)
        assert result == {"a": True}
        assert len(repair_log) == 1
        assert repair_log[0].kind == RepairKind.PYTHON_LITERAL

    def test_python_false(self, repair_log: list) -> None:
        """Python False converted to JSON false."""
        result = loads_relaxed('{"a": False}', repair_log=repair_log)
        assert result == {"a": False}
        assert len(repair_log) == 1

    def test_python_none(self, repair_log: list) -> None:
        """Python None converted to JSON null."""
        result = loads_relaxed('{"a": None}', repair_log=repair_log)
        assert result == {"a": None}
        assert len(repair_log) == 1


class TestMultipleLiterals:
    """Test multiple Python literals."""

    def test_mixed_literals(self, repair_log: list) -> None:
        """Multiple Python literals in one object."""
        result = loads_relaxed(
            '{"a": True, "b": False, "c": None}',
            repair_log=repair_log,
        )
        assert result == {"a": True, "b": False, "c": None}
        assert len(repair_log) == 3

    def test_in_array(self, repair_log: list) -> None:
        """Python literals in array."""
        result = loads_relaxed("[True, False, None]", repair_log=repair_log)
        assert result == [True, False, None]
        assert len(repair_log) == 3


class TestNotConverted:
    """Test cases where literals should NOT be converted."""

    def test_string_true_not_converted(self, repair_log: list) -> None:
        """'True' inside string not converted."""
        result = loads_relaxed('{"a": "True"}', repair_log=repair_log)
        assert result == {"a": "True"}
        assert len(repair_log) == 0  # No repairs

    def test_string_false_not_converted(self, repair_log: list) -> None:
        """'False' inside string not converted."""
        result = loads_relaxed('{"a": "False"}', repair_log=repair_log)
        assert result == {"a": "False"}

    def test_partial_match_not_converted(self, repair_log: list) -> None:
        """Partial matches like 'Trueish' not converted."""
        # This should error because Trueish is not valid JSON
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": Trueish}', repair_log=repair_log)


class TestWordBoundaries:
    """Test word boundary detection."""

    def test_true_at_start(self, repair_log: list) -> None:
        """True at start of value position."""
        result = loads_relaxed('[True]', repair_log=repair_log)
        assert result == [True]

    def test_true_at_end(self, repair_log: list) -> None:
        """True at end of input."""
        result = loads_relaxed('True', repair_log=repair_log)
        assert result is True


class TestWithOtherFeatures:
    """Test Python literals with other V2 features."""

    def test_with_unquoted_keys(self, repair_log: list) -> None:
        """Python literals with unquoted keys."""
        result = loads_relaxed(
            '{active: True, enabled: False}',
            repair_log=repair_log,
        )
        assert result == {"active": True, "enabled": False}

    def test_with_single_quotes(self, repair_log: list) -> None:
        """Python literals with single-quoted strings."""
        result = loads_relaxed(
            "{'flag': True}",
            repair_log=repair_log,
        )
        assert result == {"flag": True}


class TestDisabledOption:
    """Test disabling Python literal conversion."""

    def test_disabled_raises_error(self) -> None:
        """Disabled option raises error on Python literals."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": True}', convert_python_literals=False)

    def test_disabled_allows_json_literals(self, repair_log: list) -> None:
        """JSON literals work when Python conversion disabled."""
        result = loads_relaxed(
            '{"a": true, "b": false, "c": null}',
            convert_python_literals=False,
            repair_log=repair_log,
        )
        assert result == {"a": True, "b": False, "c": None}


class TestRepairLog:
    """Test repair log for Python literal conversion."""

    def test_repair_log_true(self, repair_log: list) -> None:
        """Repair log for True."""
        loads_relaxed('{"a": True}', repair_log=repair_log)
        repair = repair_log[0]
        assert repair.original == "True"
        assert repair.replacement == "true"
        assert "True" in repair.message

    def test_repair_log_none(self, repair_log: list) -> None:
        """Repair log for None."""
        loads_relaxed('{"a": None}', repair_log=repair_log)
        repair = repair_log[0]
        assert repair.original == "None"
        assert repair.replacement == "null"
