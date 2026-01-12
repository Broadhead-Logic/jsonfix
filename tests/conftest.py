"""Shared fixtures for jsonfix tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def repair_log() -> list:
    """Fresh repair log list for each test."""
    return []


@pytest.fixture
def smart_double_quotes() -> dict[str, str]:
    """Unicode smart double quotes."""
    return {
        "left": "\u201c",  # "
        "right": "\u201d",  # "
    }


@pytest.fixture
def smart_single_quotes() -> dict[str, str]:
    """Unicode smart single quotes."""
    return {
        "left": "\u2018",  # '
        "right": "\u2019",  # '
    }


@pytest.fixture
def sample_valid_json() -> list[str]:
    """Collection of valid JSON samples."""
    return [
        "{}",
        "[]",
        "null",
        "true",
        "false",
        "42",
        "-42",
        "3.14",
        '"hello"',
        '{"a": 1, "b": 2}',
        "[1, 2, 3]",
        '{"a": {"b": {"c": 1}}}',
        '[[1, 2], [3, 4]]',
        '{"a": [1, {"b": 2}]}',
    ]


@pytest.fixture
def sample_relaxed_json() -> list[tuple[str, object, int]]:
    """Collection of relaxed JSON samples with expected results.

    Each tuple is (input, expected_output, repair_count).
    """
    return [
        ('{"a": 1,}', {"a": 1}, 1),
        ("[1, 2, 3,]", [1, 2, 3], 1),
        ('{"a": 1} // comment', {"a": 1}, 1),
        ("// comment\n{}", {}, 1),
        ('/* comment */{"a": 1}', {"a": 1}, 1),
        ('{"a": 1} # comment', {"a": 1}, 1),
    ]
