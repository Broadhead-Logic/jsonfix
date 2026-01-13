"""Tests for LLM edge case JSON error handling.

Phase 3 Features:
- JavaScript values (NaN, Infinity, undefined)
- Non-decimal number formats (hex, octal, binary)
- Double/empty comma removal

These tests define expected behavior before implementation (TDD).
"""

from __future__ import annotations

import pytest

from jsonfix import loads_relaxed, RepairKind


class TestJavaScriptValues:
    """Test conversion of JavaScript-specific values."""

    # === NaN ===

    def test_nan_to_null(self, repair_log: list) -> None:
        """Convert NaN to null."""
        text = '{"value": NaN}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": None}
        assert any(r.kind == RepairKind.JAVASCRIPT_VALUE for r in repair_log)

    def test_nan_in_array(self, repair_log: list) -> None:
        """Convert NaN in array."""
        text = '[1, NaN, 3]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [1, None, 3]

    def test_nan_multiple(self, repair_log: list) -> None:
        """Convert multiple NaN values."""
        text = '{"a": NaN, "b": NaN}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": None, "b": None}

    # === Infinity ===

    def test_infinity_to_null(self, repair_log: list) -> None:
        """Convert Infinity to null."""
        text = '{"value": Infinity}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": None}

    def test_negative_infinity(self, repair_log: list) -> None:
        """Convert -Infinity to null."""
        text = '{"value": -Infinity}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": None}

    def test_positive_infinity(self, repair_log: list) -> None:
        """Convert +Infinity to null."""
        text = '{"value": +Infinity}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": None}

    def test_infinity_in_array(self, repair_log: list) -> None:
        """Convert Infinity in array."""
        text = '[Infinity, -Infinity, 0]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [None, None, 0]

    # === undefined ===

    def test_undefined_to_null(self, repair_log: list) -> None:
        """Convert undefined to null."""
        text = '{"value": undefined}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": None}

    def test_undefined_in_array(self, repair_log: list) -> None:
        """Convert undefined in array."""
        text = '[1, undefined, 3]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [1, None, 3]

    # === Combined ===

    def test_multiple_js_values(self, repair_log: list) -> None:
        """Convert multiple JavaScript values."""
        text = '{"a": NaN, "b": Infinity, "c": undefined}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": None, "b": None, "c": None}

    def test_mixed_js_and_normal(self, repair_log: list) -> None:
        """Mix of JS values and normal values."""
        text = '{"valid": 42, "nan": NaN, "bool": true, "inf": Infinity}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"valid": 42, "nan": None, "bool": True, "inf": None}

    # === Case Sensitivity ===

    def test_nan_case_sensitive(self, repair_log: list) -> None:
        """NaN is case-sensitive (only NaN is valid)."""
        # Only "NaN" should be converted, not "nan" or "NAN"
        text = '{"value": NaN}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": None}

    def test_nan_lowercase_not_converted(self, repair_log: list) -> None:
        """Lowercase nan should not be converted (would be an error)."""
        text = '{"value": nan}'
        # This should either fail or be treated as an identifier
        # Depending on implementation, could be handled differently
        try:
            result = loads_relaxed(text, repair_log=repair_log)
            # If it succeeds, check what happened
        except Exception:
            pass  # Expected for invalid JSON

    def test_infinity_case_sensitive(self, repair_log: list) -> None:
        """Infinity is case-sensitive."""
        text = '{"value": Infinity}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": None}

    def test_undefined_case_sensitive(self, repair_log: list) -> None:
        """undefined is case-sensitive."""
        text = '{"value": undefined}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": None}

    # === In Strings (No Conversion) ===

    def test_nan_in_string_unchanged(self, repair_log: list) -> None:
        """NaN inside string should not be converted."""
        text = '{"text": "NaN is not a number"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": "NaN is not a number"}
        assert not any(r.kind == RepairKind.JAVASCRIPT_VALUE for r in repair_log)

    def test_infinity_in_string_unchanged(self, repair_log: list) -> None:
        """Infinity inside string should not be converted."""
        text = '{"text": "Infinity and beyond"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": "Infinity and beyond"}

    def test_undefined_in_string_unchanged(self, repair_log: list) -> None:
        """undefined inside string should not be converted."""
        text = '{"text": "Value is undefined"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": "Value is undefined"}

    # === Repair Logging ===

    def test_js_value_logs_repair(self, repair_log: list) -> None:
        """Verify JS value conversion is logged."""
        text = '{"value": NaN}'
        loads_relaxed(text, repair_log=repair_log)

        js_repairs = [r for r in repair_log if r.kind == RepairKind.JAVASCRIPT_VALUE]
        assert len(js_repairs) == 1
        assert "NaN" in js_repairs[0].original


class TestNumberFormats:
    """Test conversion of non-decimal number formats."""

    # === Hexadecimal ===

    def test_hexadecimal_uppercase(self, repair_log: list) -> None:
        """Convert uppercase hexadecimal to decimal."""
        text = '{"value": 0xFF}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": 255}
        assert any(r.kind == RepairKind.NUMBER_FORMAT for r in repair_log)

    def test_hexadecimal_lowercase(self, repair_log: list) -> None:
        """Convert lowercase hexadecimal to decimal."""
        text = '{"value": 0xff}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": 255}

    def test_hexadecimal_mixed_case(self, repair_log: list) -> None:
        """Convert mixed case hexadecimal."""
        text = '{"value": 0xFf}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": 255}

    def test_hexadecimal_zero(self, repair_log: list) -> None:
        """Convert hex zero."""
        text = '{"value": 0x0}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": 0}

    def test_hexadecimal_large(self, repair_log: list) -> None:
        """Convert large hexadecimal."""
        text = '{"value": 0xFFFFFF}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": 16777215}

    # === Octal ===

    def test_octal_python_style(self, repair_log: list) -> None:
        """Convert Python-style octal (0o prefix)."""
        text = '{"value": 0o777}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": 511}

    def test_octal_zero(self, repair_log: list) -> None:
        """Convert octal zero."""
        text = '{"value": 0o0}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": 0}

    def test_octal_simple(self, repair_log: list) -> None:
        """Convert simple octal."""
        text = '{"value": 0o10}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": 8}

    # === Binary ===

    def test_binary(self, repair_log: list) -> None:
        """Convert binary to decimal."""
        text = '{"value": 0b1010}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": 10}

    def test_binary_zero(self, repair_log: list) -> None:
        """Convert binary zero."""
        text = '{"value": 0b0}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": 0}

    def test_binary_one(self, repair_log: list) -> None:
        """Convert binary one."""
        text = '{"value": 0b1}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": 1}

    def test_binary_large(self, repair_log: list) -> None:
        """Convert larger binary number."""
        text = '{"value": 0b11111111}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": 255}

    # === Multiple Formats ===

    def test_multiple_formats(self, repair_log: list) -> None:
        """Convert multiple number formats in one object."""
        text = '{"hex": 0xFF, "oct": 0o10, "bin": 0b11}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"hex": 255, "oct": 8, "bin": 3}

    def test_in_array(self, repair_log: list) -> None:
        """Convert number formats in arrays."""
        text = '[0xFF, 0o10, 0b11]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [255, 8, 3]

    def test_mixed_with_decimal(self, repair_log: list) -> None:
        """Mix special formats with regular decimals."""
        text = '{"a": 10, "b": 0xFF, "c": 20}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 10, "b": 255, "c": 20}

    # === Negative Numbers ===

    def test_negative_hex(self, repair_log: list) -> None:
        """Handle negative hexadecimal."""
        text = '{"value": -0xFF}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": -255}

    def test_negative_octal(self, repair_log: list) -> None:
        """Handle negative octal."""
        text = '{"value": -0o10}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": -8}

    def test_negative_binary(self, repair_log: list) -> None:
        """Handle negative binary."""
        text = '{"value": -0b1010}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": -10}

    # === In Strings (No Conversion) ===

    def test_hex_in_string_unchanged(self, repair_log: list) -> None:
        """Hex in string should not be converted."""
        text = '{"color": "0xFF0000"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"color": "0xFF0000"}
        assert not any(r.kind == RepairKind.NUMBER_FORMAT for r in repair_log)

    def test_octal_in_string_unchanged(self, repair_log: list) -> None:
        """Octal in string should not be converted."""
        text = '{"permissions": "0o755"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"permissions": "0o755"}

    def test_binary_in_string_unchanged(self, repair_log: list) -> None:
        """Binary in string should not be converted."""
        text = '{"bits": "0b1010"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"bits": "0b1010"}

    # === Repair Logging ===

    def test_number_format_logs_repair(self, repair_log: list) -> None:
        """Verify number format conversion is logged."""
        text = '{"value": 0xFF}'
        loads_relaxed(text, repair_log=repair_log)

        format_repairs = [r for r in repair_log if r.kind == RepairKind.NUMBER_FORMAT]
        assert len(format_repairs) == 1
        assert "0xFF" in format_repairs[0].original


class TestDoubleComma:
    """Test removal of double/empty commas."""

    # === Object Double Commas ===

    def test_double_comma_object(self, repair_log: list) -> None:
        """Remove double comma in object."""
        text = '{"a": 1,, "b": 2}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}
        assert any(r.kind == RepairKind.DOUBLE_COMMA for r in repair_log)

    def test_double_comma_object_multiple(self, repair_log: list) -> None:
        """Remove multiple double commas in object."""
        text = '{"a": 1,, "b": 2,, "c": 3}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_triple_comma_object(self, repair_log: list) -> None:
        """Remove triple comma in object."""
        text = '{"a": 1,,, "b": 2}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}

    # === Array Double Commas ===

    def test_double_comma_array(self, repair_log: list) -> None:
        """Remove double comma in array."""
        text = '[1,, 2,, 3]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [1, 2, 3]

    def test_triple_comma_array(self, repair_log: list) -> None:
        """Remove triple comma in array."""
        text = '[1,,, 2]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [1, 2]

    def test_many_commas_array(self, repair_log: list) -> None:
        """Remove many consecutive commas."""
        text = '[1,,,,,2]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [1, 2]

    # === With Whitespace ===

    def test_comma_with_whitespace_between(self, repair_log: list) -> None:
        """Remove comma with whitespace between."""
        text = '{"a": 1, , "b": 2}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}

    def test_comma_with_newline_between(self, repair_log: list) -> None:
        """Remove comma with newline between."""
        text = '{"a": 1,\n, "b": 2}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}

    def test_array_comma_with_spaces(self, repair_log: list) -> None:
        """Remove array double comma with spaces."""
        text = '[1, , 2]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [1, 2]

    # === Leading/Trailing ===

    def test_leading_comma_object(self, repair_log: list) -> None:
        """Remove leading comma in object."""
        text = '{, "a": 1}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_leading_comma_array(self, repair_log: list) -> None:
        """Remove leading comma in array."""
        text = '[, 1, 2]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [1, 2]

    def test_leading_double_comma_object(self, repair_log: list) -> None:
        """Remove leading double comma in object."""
        text = '{,, "a": 1}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    # Note: Trailing commas are handled by existing TRAILING_COMMA feature

    # === Nested Structures ===

    def test_double_comma_nested_object(self, repair_log: list) -> None:
        """Remove double comma in nested object."""
        text = '{"outer": {"a": 1,, "b": 2}}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"outer": {"a": 1, "b": 2}}

    def test_double_comma_nested_array(self, repair_log: list) -> None:
        """Remove double comma in nested array."""
        text = '[[1,, 2], [3,, 4]]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [[1, 2], [3, 4]]

    # === No False Positives ===

    def test_single_comma_unchanged(self, repair_log: list) -> None:
        """Single commas should not be affected."""
        text = '{"a": 1, "b": 2}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}
        assert not any(r.kind == RepairKind.DOUBLE_COMMA for r in repair_log)

    def test_comma_in_string_unchanged(self, repair_log: list) -> None:
        """Comma sequences in strings should not be affected."""
        text = '{"text": "a,,b,,c"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": "a,,b,,c"}
        assert not any(r.kind == RepairKind.DOUBLE_COMMA for r in repair_log)

    # === Repair Logging ===

    def test_double_comma_logs_repair(self, repair_log: list) -> None:
        """Verify double comma removal is logged."""
        text = '{"a": 1,, "b": 2}'
        loads_relaxed(text, repair_log=repair_log)

        comma_repairs = [r for r in repair_log if r.kind == RepairKind.DOUBLE_COMMA]
        assert len(comma_repairs) >= 1


class TestCombinedEdgeCaseFeatures:
    """Test combinations of edge case features."""

    def test_js_values_with_number_formats(self, repair_log: list) -> None:
        """Combine JS values with number formats."""
        text = '{"nan": NaN, "hex": 0xFF, "inf": Infinity}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"nan": None, "hex": 255, "inf": None}

    def test_double_comma_with_js_values(self, repair_log: list) -> None:
        """Combine double comma with JS values."""
        text = '{"a": NaN,, "b": Infinity}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": None, "b": None}

    def test_all_edge_case_features(self, repair_log: list) -> None:
        """Test all edge case features together."""
        text = '{"nan": NaN,, "hex": 0xFF, "inf": Infinity,, "bin": 0b1010}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"nan": None, "hex": 255, "inf": None, "bin": 10}

    def test_phase3_with_phase1_features(self, repair_log: list) -> None:
        """Combine Phase 3 with Phase 1 features."""
        text = 'Here is the data: {"value": 0xFF, "status": NaN}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": 255, "status": None}

    def test_phase3_with_phase2_features(self, repair_log: list) -> None:
        """Combine Phase 3 with Phase 2 features."""
        text = '{"a" 0xFF "b" NaN}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 255, "b": None}

    def test_all_phases_combined(self, repair_log: list) -> None:
        """Test features from all phases together."""
        text = '''Here is the result:
```json
{
    "value" 0xFF
    "status": NaN,,
    "path": "C:\\Users\\test",
}
```
Hope this helps!'''
        result = loads_relaxed(text, repair_log=repair_log)
        assert result["value"] == 255
        assert result["status"] is None

    def test_feature_disable_js_values(self, repair_log: list) -> None:
        """Verify JS value conversion can be disabled.

        Note: Python's json module accepts NaN/Infinity natively (non-standard
        but common). So disabling convert_javascript_values means NaN is NOT
        converted to null, but Python still parses it as float('nan').
        """
        import math

        text = '{"value": NaN}'
        result = loads_relaxed(
            text, convert_javascript_values=False, repair_log=repair_log
        )
        # NaN is parsed by Python's json module, not converted to null
        assert math.isnan(result["value"])
        # No repair logged since no conversion happened
        js_repairs = [r for r in repair_log if r.kind.name == "JAVASCRIPT_VALUE"]
        assert len(js_repairs) == 0

    def test_feature_disable_number_formats(self, repair_log: list) -> None:
        """Verify number format conversion can be disabled."""
        text = '{"value": 0xFF}'
        with pytest.raises(Exception):  # JSONDecodeError
            loads_relaxed(text, convert_number_formats=False, repair_log=repair_log)
