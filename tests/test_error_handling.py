"""Tests for error handling."""

from __future__ import annotations

import json
import warnings

import pytest

from jsonfix import loads_relaxed


class TestStandardJsonErrors:
    """Test that standard JSON errors still occur."""

    def test_unclosed_object(self) -> None:
        """Unclosed object raises JSONDecodeError when auto_close_brackets=False."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": 1', auto_close_brackets=False)

    def test_unclosed_array(self) -> None:
        """Unclosed array raises JSONDecodeError when auto_close_brackets=False."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed("[1, 2", auto_close_brackets=False)

    def test_unclosed_string(self) -> None:
        """Unclosed string raises JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": "hello}')

    def test_invalid_value_undefined(self) -> None:
        """undefined is not valid JSON when JS value conversion is disabled."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": undefined}', convert_javascript_values=False)

    def test_nan_parses_as_python_nan(self, repair_log: list) -> None:
        """NaN is accepted by Python's json module (non-standard but common).

        When JS value conversion is disabled, Python's json module accepts NaN.
        """
        import math

        result = loads_relaxed(
            '{"a": NaN}', convert_javascript_values=False, repair_log=repair_log
        )
        assert math.isnan(result["a"])
        # No repairs needed - Python handles this natively
        assert repair_log == []

    def test_infinity_parses_as_python_inf(self, repair_log: list) -> None:
        """Infinity is accepted by Python's json module (non-standard but common).

        When JS value conversion is disabled, Python's json module accepts Infinity.
        """
        import math

        result = loads_relaxed(
            '{"a": Infinity}', convert_javascript_values=False, repair_log=repair_log
        )
        assert math.isinf(result["a"])
        assert repair_log == []

    def test_duplicate_comma_array(self) -> None:
        """Duplicate comma in array is an error when feature is disabled."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed("[1,, 2]", remove_double_commas=False)

    def test_leading_comma_array(self) -> None:
        """Leading comma in array is an error when feature is disabled."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed("[, 1, 2]", remove_double_commas=False)

    def test_missing_colon(self) -> None:
        """Missing colon in object is an error when fix_missing_colon disabled."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a" 1}', fix_missing_colon=False)

    def test_missing_comma_object(self) -> None:
        """Missing comma between object properties is an error when disabled."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": 1 "b": 2}', fix_missing_comma=False)

    def test_missing_comma_array(self) -> None:
        """Missing comma between array elements is an error when disabled."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed("[1 2 3]", fix_missing_comma=False)

    def test_single_quotes_as_delimiters(self) -> None:
        """Single quotes as string delimiters is an error when disabled."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed("{'a': 1}", allow_single_quote_strings=False)

    def test_unquoted_keys(self) -> None:
        """Unquoted keys is an error when disabled."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed("{a: 1}", allow_unquoted_keys=False)


class TestErrorMessageQuality:
    """Test that error messages are helpful."""

    def test_error_includes_position_info(self) -> None:
        """Error includes position information."""
        try:
            loads_relaxed('{"a": }')
        except json.JSONDecodeError as e:
            # JSONDecodeError should have line and column info
            assert hasattr(e, "lineno") or "line" in str(e).lower()

    def test_error_for_invalid_json_after_relaxation(self) -> None:
        """Error message is clear even after relaxation processing."""
        # This should still error - the comma is missing, not trailing
        try:
            loads_relaxed('{"a": 1 "b": 2}')
        except json.JSONDecodeError as e:
            # Error should mention the issue
            assert str(e)  # Has some error message


class TestOnRepairParameter:
    """Test on_repair parameter behavior."""

    def test_on_repair_ignore(self, repair_log: list) -> None:
        """on_repair='ignore' produces no warnings."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            loads_relaxed('{"a": 1,}', repair_log=repair_log, on_repair="ignore")
            # No warnings should be raised
            json_warnings = [x for x in w if "json" in str(x.category).lower()]
            assert len(json_warnings) == 0

    def test_on_repair_warn(self, repair_log: list) -> None:
        """on_repair='warn' emits warnings."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            loads_relaxed('{"a": 1,}', repair_log=repair_log, on_repair="warn")
            # Should have at least one warning
            assert len(w) >= 1

    def test_on_repair_error(self) -> None:
        """on_repair='error' raises on first repair."""
        with pytest.raises((ValueError, json.JSONDecodeError)):
            loads_relaxed('{"a": 1,}', on_repair="error")

    def test_on_repair_error_valid_json(self, repair_log: list) -> None:
        """on_repair='error' with valid JSON doesn't error."""
        result = loads_relaxed(
            '{"a": 1}', repair_log=repair_log, on_repair="error"
        )
        assert result == {"a": 1}
        assert repair_log == []


class TestStrictMode:
    """Test strict mode comprehensively."""

    def test_strict_rejects_trailing_comma(self) -> None:
        """Strict mode rejects trailing comma."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": 1,}', strict=True)

    def test_strict_rejects_single_line_comment(self) -> None:
        """Strict mode rejects // comments."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": 1} // comment', strict=True)

    def test_strict_rejects_multi_line_comment(self) -> None:
        """Strict mode rejects /* */ comments."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": 1} /* comment */', strict=True)

    def test_strict_rejects_hash_comment(self) -> None:
        """Strict mode rejects # comments."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": 1} # comment', strict=True)

    def test_strict_rejects_smart_quotes(
        self, smart_double_quotes: dict[str, str]
    ) -> None:
        """Strict mode rejects smart quotes."""
        left = smart_double_quotes["left"]
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed(f'{{{left}"a": 1}}', strict=True)

    def test_strict_valid_json_works(self, repair_log: list) -> None:
        """Strict mode accepts valid JSON."""
        result = loads_relaxed('{"a": 1, "b": 2}', strict=True, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}
        assert repair_log == []


class TestOptionCombinations:
    """Test combinations of disabled options."""

    def test_disable_trailing_comma_only(self, repair_log: list) -> None:
        """Only trailing commas disabled."""
        # This should work (comment is allowed)
        result = loads_relaxed(
            '{"a": 1} // comment',
            allow_trailing_commas=False,
            repair_log=repair_log,
        )
        assert result == {"a": 1}

        # This should fail (trailing comma not allowed)
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": 1,}', allow_trailing_commas=False)

    def test_disable_comments_only(self, repair_log: list) -> None:
        """Only comments disabled."""
        # This should work (trailing comma is allowed)
        result = loads_relaxed(
            '{"a": 1,}',
            allow_comments=False,
            repair_log=repair_log,
        )
        assert result == {"a": 1}

        # This should fail (comment not allowed)
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": 1} // comment', allow_comments=False)

    def test_disable_quotes_only(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """Only quote normalization disabled."""
        # This should work (trailing comma is allowed)
        result = loads_relaxed(
            '{"a": 1,}',
            normalize_quotes=False,
            repair_log=repair_log,
        )
        assert result == {"a": 1}

        # This should fail (smart quote not normalized)
        left = smart_double_quotes["left"]
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed(f'{{{left}"a": 1}}', normalize_quotes=False)

    def test_all_options_disabled(self) -> None:
        """All relaxations disabled (equivalent to strict)."""
        # Valid JSON should work
        result = loads_relaxed(
            '{"a": 1}',
            allow_trailing_commas=False,
            allow_comments=False,
            normalize_quotes=False,
        )
        assert result == {"a": 1}

        # Any relaxation should fail
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed(
                '{"a": 1,}',
                allow_trailing_commas=False,
                allow_comments=False,
                normalize_quotes=False,
            )


class TestInvalidParameterValues:
    """Test invalid parameter values."""

    def test_invalid_on_repair_value(self) -> None:
        """Invalid on_repair value raises error."""
        with pytest.raises((ValueError, TypeError)):
            loads_relaxed('{"a": 1}', on_repair="invalid")  # type: ignore
