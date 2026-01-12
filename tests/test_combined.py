"""Tests for multiple relaxations combined."""

from __future__ import annotations

import pytest

from jsonfix import loads_relaxed, RepairKind


class TestTwoRelaxations:
    """Test combinations of two relaxations."""

    def test_comments_and_trailing_comma(self, repair_log: list) -> None:
        """Comment and trailing comma together."""
        json_str = '{"a": 1, // comment\n}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 2
        kinds = {r.kind for r in repair_log}
        assert RepairKind.SINGLE_LINE_COMMENT in kinds
        assert RepairKind.TRAILING_COMMA in kinds

    def test_smart_quotes_and_trailing_comma(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """Smart quotes and trailing comma together."""
        left = smart_double_quotes["left"]
        right = smart_double_quotes["right"]
        json_str = f'{{{left}a{right}: 1,}}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1}
        kinds = {r.kind for r in repair_log}
        assert RepairKind.SMART_QUOTE in kinds
        assert RepairKind.TRAILING_COMMA in kinds

    def test_comments_and_smart_quotes(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """Comment and smart quotes together."""
        left = smart_double_quotes["left"]
        right = smart_double_quotes["right"]
        json_str = f'{{{left}a{right}: {left}hi{right}}} // comment'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": "hi"}
        kinds = {r.kind for r in repair_log}
        assert RepairKind.SMART_QUOTE in kinds
        assert RepairKind.SINGLE_LINE_COMMENT in kinds


class TestAllThreeRelaxations:
    """Test all three relaxations combined."""

    def test_all_relaxations_simple(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """All three relaxations in simple structure."""
        left = smart_double_quotes["left"]
        right = smart_double_quotes["right"]
        json_str = f'{{{left}a{right}: 1, /* comment */}} // end'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1}
        kinds = {r.kind for r in repair_log}
        assert RepairKind.SMART_QUOTE in kinds
        assert RepairKind.MULTI_LINE_COMMENT in kinds

    def test_all_relaxations_complex(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """All relaxations in complex nested structure."""
        left = smart_double_quotes["left"]
        right = smart_double_quotes["right"]
        json_str = f"""{{
            // Header comment
            {left}users{right}: [
                /* First user */
                {{{left}name{right}: {left}Alice{right},}},
                {{{left}name{right}: {left}Bob{right},}},  # inline comment
            ],
        }}"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["users"][0]["name"] == "Alice"
        assert result["users"][1]["name"] == "Bob"
        assert len(repair_log) > 5  # Multiple repairs


class TestRealWorldPasteScenarios:
    """Test real-world paste scenarios."""

    def test_llm_output_typical(self, repair_log: list) -> None:
        """Typical LLM JSON output with issues."""
        json_str = """{
            "response": "Here is the data",
            "items": ["a", "b", "c",],
            "count": 3,
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["response"] == "Here is the data"
        assert result["items"] == ["a", "b", "c"]
        assert result["count"] == 3
        # Should have 2 trailing commas repaired
        trailing_repairs = [
            r for r in repair_log if r.kind == RepairKind.TRAILING_COMMA
        ]
        assert len(trailing_repairs) == 2

    def test_dashboard_export(self, repair_log: list) -> None:
        """JSON exported from dashboards often has trailing commas."""
        json_str = """{
            "metrics": {
                "cpu": 45.5,
                "memory": 72.3,
                "disk": 89.1,
            },
            "timestamp": "2025-01-12T10:30:00Z",
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["metrics"]["cpu"] == 45.5
        assert len(repair_log) > 0

    def test_config_file_style(self, repair_log: list) -> None:
        """JSONC-style config file."""
        json_str = """{
            // Database configuration
            "database": {
                "host": "localhost",
                "port": 5432,
                /* Connection pool settings */
                "pool_size": 10,
            },
            // Feature flags
            "features": {
                "new_ui": true,
                "beta_api": false,
            },
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["database"]["host"] == "localhost"
        assert result["features"]["new_ui"] is True
        # Should have comments and trailing commas
        comment_repairs = [
            r
            for r in repair_log
            if r.kind
            in (
                RepairKind.SINGLE_LINE_COMMENT,
                RepairKind.MULTI_LINE_COMMENT,
            )
        ]
        assert len(comment_repairs) >= 3


class TestRepairLogOrdering:
    """Test repair log ordering and accuracy."""

    def test_repair_log_contains_all_repairs(self, repair_log: list) -> None:
        """All repairs are logged (order depends on processing stages)."""
        # Note: Repairs are logged in processing order (quote norm -> comments -> commas)
        # not necessarily in position order in the original string
        json_str = '// first\n{"a": 1,} // second'
        loads_relaxed(json_str, repair_log=repair_log)
        # Should have 2 comments and 1 trailing comma
        assert len(repair_log) == 3
        kinds = [r.kind for r in repair_log]
        assert kinds.count(RepairKind.SINGLE_LINE_COMMENT) == 2
        assert kinds.count(RepairKind.TRAILING_COMMA) == 1

    def test_repair_log_all_types_present(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """All repair types can be present in one log."""
        left = smart_double_quotes["left"]
        right = smart_double_quotes["right"]
        json_str = f'// comment\n{{{left}a{right}: 1,}} # end'
        loads_relaxed(json_str, repair_log=repair_log)
        kinds = {r.kind for r in repair_log}
        assert RepairKind.SINGLE_LINE_COMMENT in kinds
        assert RepairKind.SMART_QUOTE in kinds
        assert RepairKind.TRAILING_COMMA in kinds
        assert RepairKind.HASH_COMMENT in kinds

    def test_repair_count_accuracy(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """Repair count exactly matches expectations."""
        left = smart_double_quotes["left"]
        right = smart_double_quotes["right"]
        # 1 // comment, 2 smart quotes, 1 trailing comma, 1 # comment
        json_str = f'// start\n{{{left}a{right}: 1,}} # end'
        loads_relaxed(json_str, repair_log=repair_log)
        assert len(repair_log) == 5  # Exact count


class TestComplexNesting:
    """Test complex nested structures with mixed relaxations."""

    def test_deeply_nested_with_all_issues(self, repair_log: list) -> None:
        """Deeply nested structure with issues at every level."""
        json_str = """{
            "level1": {
                // Comment at level 1
                "level2": {
                    /* Comment at level 2 */
                    "level3": {
                        # Comment at level 3
                        "data": [1, 2, 3,],
                    },
                },
            },
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["level1"]["level2"]["level3"]["data"] == [1, 2, 3]
        assert len(repair_log) >= 6  # At least 3 comments + 3 trailing commas

    def test_array_of_objects_with_issues(self, repair_log: list) -> None:
        """Array of objects each with trailing commas."""
        json_str = """[
            {"id": 1, "name": "a",},
            {"id": 2, "name": "b",},
            {"id": 3, "name": "c",},
        ]"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert len(result) == 3
        assert result[0]["id"] == 1
        # 3 inner trailing commas + 1 outer trailing comma = 4
        trailing_repairs = [
            r for r in repair_log if r.kind == RepairKind.TRAILING_COMMA
        ]
        assert len(trailing_repairs) == 4
