"""Tests for V2: Compatibility with relaxed JSON inputs (LLM output, configs)."""

from __future__ import annotations

from jsonfix import loads_relaxed


class TestRelaxedInputCompatibility:
    """Test relaxed JSON inputs commonly seen in LLM output and configs."""

    def test_single_quoted_strings(self, repair_log: list) -> None:
        """Single-quoted strings are converted to double-quoted."""
        result = loads_relaxed("{'name': 'test'}", repair_log=repair_log)
        assert result == {"name": "test"}
        assert len(repair_log) == 2  # Two single-quoted strings

    def test_unquoted_key_with_single_quote_value(self, repair_log: list) -> None:
        """Unquoted key with single-quoted value."""
        result = loads_relaxed("{name: 'test'}", repair_log=repair_log)
        assert result == {"name": "test"}

    def test_python_booleans(self, repair_log: list) -> None:
        """Python True/False/None are converted to JSON literals."""
        result = loads_relaxed(
            '{"valid": True, "active": False, "data": None}',
            repair_log=repair_log,
        )
        assert result == {"valid": True, "active": False, "data": None}
        assert len(repair_log) == 3

    def test_missing_bracket_at_end(self, repair_log: list) -> None:
        """Missing brackets at end are auto-closed."""
        result = loads_relaxed('{"incomplete": 1', repair_log=repair_log)
        assert result == {"incomplete": 1}

    def test_truncated_with_ellipsis(self, repair_log: list) -> None:
        """Truncation markers like ... are removed."""
        result = loads_relaxed("[1, 2, ...]", repair_log=repair_log)
        assert result == [1, 2]

    def test_llm_output_typical(self, repair_log: list) -> None:
        """Typical LLM output with multiple issues."""
        llm_json = """{
            'response': 'Here is the data',
            items: [1, 2, 3, ...],
            valid: True,
        }"""
        result = loads_relaxed(llm_json, repair_log=repair_log)
        assert result["response"] == "Here is the data"
        assert result["items"] == [1, 2, 3]
        assert result["valid"] is True

    def test_config_file_style(self, repair_log: list) -> None:
        """Config file with comments and trailing commas."""
        config = """{
            // Database settings
            "host": "localhost",
            "port": 5432,
            /* These are optional */
            "timeout": 30,
        }"""
        result = loads_relaxed(config, repair_log=repair_log)
        assert result["host"] == "localhost"
        assert result["port"] == 5432
        assert result["timeout"] == 30


class TestCombinedIssues:
    """Test JSON with multiple issues combined."""

    def test_all_v2_features_combined(self, repair_log: list) -> None:
        """All V2 features used together."""
        messy_json = """{
            name: 'John',
            active: True,
            items: [1, 2, ...],
        """
        result = loads_relaxed(messy_json, repair_log=repair_log)
        assert result == {"name": "John", "active": True, "items": [1, 2]}

    def test_deeply_nested_mess(self, repair_log: list) -> None:
        """Deeply nested structure with various issues."""
        result = loads_relaxed(
            "{outer: {inner: {value: True}}}",
            repair_log=repair_log,
        )
        assert result == {"outer": {"inner": {"value": True}}}

    def test_api_response_simulation(self, repair_log: list) -> None:
        """Simulated API response with common issues."""
        api_response = """{
            status: 'success',
            data: {
                users: [
                    {name: 'Alice', active: True},
                    {name: 'Bob', active: False},
                ],
                total: 2,
            },
        }"""
        result = loads_relaxed(api_response, repair_log=repair_log)
        assert result["status"] == "success"
        assert len(result["data"]["users"]) == 2
        assert result["data"]["users"][0]["name"] == "Alice"


class TestRepairLogging:
    """Test that all repairs are logged correctly."""

    def test_multiple_repair_types_logged(self, repair_log: list) -> None:
        """All repair types are logged for complex input."""
        loads_relaxed("{key: 'value', flag: True,}", repair_log=repair_log)

        repair_kinds = {r.kind.name for r in repair_log}
        assert "UNQUOTED_KEY" in repair_kinds
        assert "SINGLE_QUOTE_STRING" in repair_kinds
        assert "PYTHON_LITERAL" in repair_kinds
        assert "TRAILING_COMMA" in repair_kinds

    def test_repairs_contain_useful_info(self, repair_log: list) -> None:
        """Each repair contains useful information."""
        loads_relaxed("{key: True}", repair_log=repair_log)

        for repair in repair_log:
            assert repair.position >= 0
            assert repair.line >= 1
            assert repair.column >= 1
            assert repair.message  # Has a message
