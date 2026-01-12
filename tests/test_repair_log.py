"""Tests for repair log accuracy and functionality."""

from __future__ import annotations

import pytest

from jsonfix import loads_relaxed, Repair, RepairKind


class TestBasicFunctionality:
    """Test basic repair log functionality."""

    def test_repair_log_none_by_default(self) -> None:
        """No error when repair_log is not provided."""
        result = loads_relaxed('{"a": 1,}')
        assert result == {"a": 1}

    def test_repair_log_empty_for_valid_json(self, repair_log: list) -> None:
        """Repair log is empty for valid JSON."""
        loads_relaxed('{"a": 1}', repair_log=repair_log)
        assert repair_log == []

    def test_repair_log_is_list(self, repair_log: list) -> None:
        """Repair log receives Repair objects."""
        loads_relaxed('{"a": 1,}', repair_log=repair_log)
        assert isinstance(repair_log, list)
        assert len(repair_log) == 1
        assert isinstance(repair_log[0], Repair)

    def test_repair_log_appends_not_replaces(self) -> None:
        """Multiple calls append to the same log."""
        log: list[Repair] = []
        loads_relaxed('{"a": 1,}', repair_log=log)
        loads_relaxed('{"b": 2,}', repair_log=log)
        assert len(log) == 2


class TestRepairObjectFields:
    """Test Repair object field values."""

    def test_repair_has_kind(self, repair_log: list) -> None:
        """Repair has kind field with RepairKind enum."""
        loads_relaxed('{"a": 1,}', repair_log=repair_log)
        repair = repair_log[0]
        assert hasattr(repair, "kind")
        assert isinstance(repair.kind, RepairKind)

    def test_repair_has_position(self, repair_log: list) -> None:
        """Repair has position field (character offset)."""
        loads_relaxed('{"a": 1,}', repair_log=repair_log)
        repair = repair_log[0]
        assert hasattr(repair, "position")
        assert isinstance(repair.position, int)
        assert repair.position >= 0

    def test_repair_has_line(self, repair_log: list) -> None:
        """Repair has line field (1-indexed)."""
        loads_relaxed('{"a": 1,}', repair_log=repair_log)
        repair = repair_log[0]
        assert hasattr(repair, "line")
        assert isinstance(repair.line, int)
        assert repair.line >= 1

    def test_repair_has_column(self, repair_log: list) -> None:
        """Repair has column field (1-indexed)."""
        loads_relaxed('{"a": 1,}', repair_log=repair_log)
        repair = repair_log[0]
        assert hasattr(repair, "column")
        assert isinstance(repair.column, int)
        assert repair.column >= 1

    def test_repair_has_original(self, repair_log: list) -> None:
        """Repair has original field."""
        loads_relaxed('// comment\n{}', repair_log=repair_log)
        repair = repair_log[0]
        assert hasattr(repair, "original")
        assert isinstance(repair.original, str)
        assert "comment" in repair.original

    def test_repair_has_replacement(self, repair_log: list) -> None:
        """Repair has replacement field."""
        loads_relaxed('{"a": 1,}', repair_log=repair_log)
        repair = repair_log[0]
        assert hasattr(repair, "replacement")
        assert isinstance(repair.replacement, str)
        # Trailing comma replacement is empty (removed)
        assert repair.replacement == ""

    def test_repair_has_message(self, repair_log: list) -> None:
        """Repair has message field (human-readable)."""
        loads_relaxed('{"a": 1,}', repair_log=repair_log)
        repair = repair_log[0]
        assert hasattr(repair, "message")
        assert isinstance(repair.message, str)
        assert len(repair.message) > 0


class TestPositionAccuracy:
    """Test position tracking accuracy."""

    def test_position_first_character(self, repair_log: list) -> None:
        """Repair at first character."""
        loads_relaxed('// comment\n{}', repair_log=repair_log)
        repair = repair_log[0]
        assert repair.position == 0
        assert repair.line == 1
        assert repair.column == 1

    def test_position_end_of_input(self, repair_log: list) -> None:
        """Repair at end of input."""
        loads_relaxed('{}// comment', repair_log=repair_log)
        repair = repair_log[0]
        assert repair.position == 2  # After {}

    def test_position_multiline(self, repair_log: list) -> None:
        """Correct line/column for multiline input."""
        json_str = '{\n  "a": 1,\n}'
        loads_relaxed(json_str, repair_log=repair_log)
        repair = repair_log[0]
        assert repair.line == 2  # Trailing comma is on line 2

    def test_position_third_line(self, repair_log: list) -> None:
        """Correct position on third line."""
        json_str = '{\n"a": 1,\n"b": 2,\n}'
        loads_relaxed(json_str, repair_log=repair_log)
        # Only 1 trailing comma - the one on line 3 before the closing }
        # The comma after "a": 1 is NOT trailing (followed by "b")
        assert len(repair_log) == 1
        assert repair_log[0].line == 3  # Trailing comma is on line 3

    def test_position_with_unicode(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """Positions are correct with unicode characters."""
        left = smart_double_quotes["left"]
        # Use smart quote as opening quote of the key (not followed by straight quote)
        json_str = f'{{{left}a": 1}}'  # {"a": 1} with smart opening quote
        loads_relaxed(json_str, repair_log=repair_log)
        repair = repair_log[0]
        # Unicode smart quote is at position 1
        assert repair.position == 1

    def test_position_after_previous_repairs(self, repair_log: list) -> None:
        """Positions are relative to original string, not modified."""
        # Important: positions should always refer to original string
        json_str = '// first\n// second\n{}'
        loads_relaxed(json_str, repair_log=repair_log)
        assert len(repair_log) == 2
        # First comment at position 0
        assert repair_log[0].position == 0
        # Second comment at original position (after first comment)
        assert repair_log[1].position > repair_log[0].position


class TestRepairKindEnum:
    """Test RepairKind enum values."""

    def test_repair_kind_trailing_comma(self, repair_log: list) -> None:
        """TRAILING_COMMA kind."""
        loads_relaxed('{"a": 1,}', repair_log=repair_log)
        assert repair_log[0].kind == RepairKind.TRAILING_COMMA

    def test_repair_kind_single_line_comment(self, repair_log: list) -> None:
        """SINGLE_LINE_COMMENT kind."""
        loads_relaxed('{"a": 1} // comment', repair_log=repair_log)
        assert repair_log[0].kind == RepairKind.SINGLE_LINE_COMMENT

    def test_repair_kind_multi_line_comment(self, repair_log: list) -> None:
        """MULTI_LINE_COMMENT kind."""
        loads_relaxed('{"a": /* comment */ 1}', repair_log=repair_log)
        assert repair_log[0].kind == RepairKind.MULTI_LINE_COMMENT

    def test_repair_kind_hash_comment(self, repair_log: list) -> None:
        """HASH_COMMENT kind."""
        loads_relaxed('{"a": 1} # comment', repair_log=repair_log)
        assert repair_log[0].kind == RepairKind.HASH_COMMENT

    def test_repair_kind_smart_quote(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """SMART_QUOTE kind."""
        left = smart_double_quotes["left"]
        # Use smart quote as opening quote of the key
        json_str = f'{{{left}a": 1}}'  # {"a": 1} with smart opening quote
        loads_relaxed(json_str, repair_log=repair_log)
        assert repair_log[0].kind == RepairKind.SMART_QUOTE


class TestRepairDataclass:
    """Test Repair dataclass behavior."""

    def test_repair_is_dataclass(self, repair_log: list) -> None:
        """Repair is a dataclass with standard behavior."""
        loads_relaxed('{"a": 1,}', repair_log=repair_log)
        repair = repair_log[0]
        # Dataclass should have __repr__
        repr_str = repr(repair)
        assert "Repair" in repr_str
        assert "kind" in repr_str

    def test_repair_equality(self, repair_log: list) -> None:
        """Two identical repairs are equal."""
        # This tests dataclass equality
        loads_relaxed('{"a": 1,}', repair_log=repair_log)
        repair1 = repair_log[0]

        repair_log2: list[Repair] = []
        loads_relaxed('{"a": 1,}', repair_log=repair_log2)
        repair2 = repair_log2[0]

        assert repair1 == repair2

    def test_repair_fields_accessible(self, repair_log: list) -> None:
        """All repair fields are accessible."""
        loads_relaxed('{"a": 1,}', repair_log=repair_log)
        repair = repair_log[0]

        # All fields should be accessible without error
        _ = repair.kind
        _ = repair.position
        _ = repair.line
        _ = repair.column
        _ = repair.original
        _ = repair.replacement
        _ = repair.message
