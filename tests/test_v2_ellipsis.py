"""Tests for V2: Ellipsis marker removal."""

from __future__ import annotations

import json

import pytest

from jsonfix import loads_relaxed, RepairKind


class TestBasicEllipsisRemoval:
    """Test basic ellipsis removal."""

    def test_array_ellipsis(self, repair_log: list) -> None:
        """Ellipsis at end of array is removed."""
        result = loads_relaxed("[1, 2, ...]", repair_log=repair_log)
        assert result == [1, 2]
        assert len(repair_log) == 1
        assert repair_log[0].kind == RepairKind.TRUNCATION_MARKER

    def test_unicode_ellipsis(self, repair_log: list) -> None:
        """Unicode ellipsis character is removed."""
        result = loads_relaxed("[1, 2, …]", repair_log=repair_log)
        assert result == [1, 2]
        assert len(repair_log) == 1

    def test_object_ellipsis(self, repair_log: list) -> None:
        """Ellipsis at end of object is removed."""
        result = loads_relaxed('{"a": 1, ...}', repair_log=repair_log)
        assert result == {"a": 1}


class TestEllipsisInNestedStructures:
    """Test ellipsis in nested structures."""

    def test_nested_array_ellipsis(self, repair_log: list) -> None:
        """Ellipsis in nested array."""
        result = loads_relaxed("[[1, 2, ...], [3, 4]]", repair_log=repair_log)
        assert result == [[1, 2], [3, 4]]
        assert len(repair_log) == 1

    def test_object_in_array_with_ellipsis(self, repair_log: list) -> None:
        """Ellipsis in array with objects."""
        result = loads_relaxed('[{"a": 1}, ...]', repair_log=repair_log)
        assert result == [{"a": 1}]


class TestEllipsisPreservedInStrings:
    """Test that ellipsis in strings is NOT removed."""

    def test_ellipsis_in_string_preserved(self, repair_log: list) -> None:
        """Ellipsis inside string value is preserved."""
        result = loads_relaxed('{"text": "Loading..."}', repair_log=repair_log)
        assert result == {"text": "Loading..."}
        assert len(repair_log) == 0  # No repairs - ellipsis in string

    def test_unicode_ellipsis_in_string_preserved(self, repair_log: list) -> None:
        """Unicode ellipsis in string is preserved."""
        result = loads_relaxed('{"text": "Loading…"}', repair_log=repair_log)
        assert result == {"text": "Loading…"}
        assert len(repair_log) == 0


class TestWithOtherFeatures:
    """Test ellipsis with other features."""

    def test_ellipsis_with_trailing_comma(self, repair_log: list) -> None:
        """Ellipsis works with trailing comma feature."""
        # The comma before ellipsis should be removed along with ellipsis
        result = loads_relaxed("[1, 2, ...]", repair_log=repair_log)
        assert result == [1, 2]

    def test_ellipsis_combined_repairs(self, repair_log: list) -> None:
        """Ellipsis combined with other repairs."""
        result = loads_relaxed("{'items': [1, 2, ...]}", repair_log=repair_log)
        assert result == {"items": [1, 2]}


class TestDisabledOption:
    """Test disabling ellipsis removal."""

    def test_disabled_causes_error(self) -> None:
        """Disabled option causes JSON error on ellipsis."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed("[1, 2, ...]", remove_ellipsis=False)

    def test_disabled_allows_other_features(self, repair_log: list) -> None:
        """Other features work when ellipsis removal disabled."""
        result = loads_relaxed(
            '{"a": 1,}',
            remove_ellipsis=False,
            repair_log=repair_log,
        )
        assert result == {"a": 1}


class TestRepairLog:
    """Test repair log for ellipsis removal."""

    def test_repair_log_records_ellipsis(self, repair_log: list) -> None:
        """Repair log records ellipsis removal."""
        loads_relaxed("[1, 2, ...]", repair_log=repair_log)
        repair = repair_log[0]
        assert repair.kind == RepairKind.TRUNCATION_MARKER
        assert "..." in repair.original or "…" in repair.original


class TestEllipsisWithWhitespace:
    """Test ellipsis with trailing whitespace."""

    def test_ascii_ellipsis_with_trailing_spaces(self, repair_log: list) -> None:
        """ASCII ellipsis followed by spaces before bracket."""
        # Covers normalizers.py line 562
        result = loads_relaxed("[1, 2, ...   ]", repair_log=repair_log)
        assert result == [1, 2]
        assert len(repair_log) == 1

    def test_ascii_ellipsis_with_trailing_newline(self, repair_log: list) -> None:
        """ASCII ellipsis followed by newline before bracket."""
        result = loads_relaxed("[1, 2, ...\n]", repair_log=repair_log)
        assert result == [1, 2]

    def test_ascii_ellipsis_with_trailing_tab(self, repair_log: list) -> None:
        """ASCII ellipsis followed by tab before bracket."""
        result = loads_relaxed("[1, 2, ...\t]", repair_log=repair_log)
        assert result == [1, 2]

    def test_unicode_ellipsis_with_trailing_spaces(self, repair_log: list) -> None:
        """Unicode ellipsis followed by spaces before bracket."""
        # Covers normalizers.py line 592
        result = loads_relaxed("[1, 2, …   ]", repair_log=repair_log)
        assert result == [1, 2]
        assert len(repair_log) == 1

    def test_unicode_ellipsis_with_trailing_newline(self, repair_log: list) -> None:
        """Unicode ellipsis followed by newline before bracket."""
        result = loads_relaxed("[1, 2, …\n]", repair_log=repair_log)
        assert result == [1, 2]

    def test_unicode_ellipsis_with_mixed_whitespace(self, repair_log: list) -> None:
        """Unicode ellipsis followed by mixed whitespace."""
        result = loads_relaxed("[1, 2, … \t\n ]", repair_log=repair_log)
        assert result == [1, 2]
