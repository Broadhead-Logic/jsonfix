"""Tests for comment stripping."""

from __future__ import annotations

import json

import pytest

from jsonfix import loads_relaxed, RepairKind


class TestSingleLineComments:
    """Test single-line // comments."""

    def test_single_line_comment_end(self, repair_log: list) -> None:
        """Comment at end of JSON."""
        result = loads_relaxed('{"a": 1} // comment', repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1
        assert repair_log[0].kind == RepairKind.SINGLE_LINE_COMMENT

    def test_single_line_comment_between(self, repair_log: list) -> None:
        """Comment between properties."""
        result = loads_relaxed('{"a": 1, // comment\n"b": 2}', repair_log=repair_log)
        assert result == {"a": 1, "b": 2}
        assert len(repair_log) == 1

    def test_single_line_comment_own_line(self, repair_log: list) -> None:
        """Comment on its own line."""
        result = loads_relaxed('// comment\n{"a": 1}', repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1

    def test_multiple_single_line_comments(self, repair_log: list) -> None:
        """Multiple single-line comments."""
        json_str = """
        // first comment
        {
            // second comment
            "a": 1
            // third comment
        }
        """
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1}
        comment_repairs = [
            r for r in repair_log if r.kind == RepairKind.SINGLE_LINE_COMMENT
        ]
        assert len(comment_repairs) == 3


class TestMultiLineComments:
    """Test multi-line /* */ comments."""

    def test_multi_line_comment_inline(self, repair_log: list) -> None:
        """Inline multi-line comment."""
        result = loads_relaxed('{"a": /* comment */ 1}', repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1
        assert repair_log[0].kind == RepairKind.MULTI_LINE_COMMENT

    def test_multi_line_comment_spanning_lines(self, repair_log: list) -> None:
        """Multi-line comment spanning multiple lines."""
        json_str = """{
            "a": /* this is
            a multi-line
            comment */ 1
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1

    def test_multi_line_comment_before_json(self, repair_log: list) -> None:
        """Multi-line comment before JSON."""
        result = loads_relaxed('/* comment */{"a": 1}', repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1

    def test_multi_line_comment_after_json(self, repair_log: list) -> None:
        """Multi-line comment after JSON."""
        result = loads_relaxed('{"a": 1}/* comment */', repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1

    def test_nested_multi_line_patterns(self, repair_log: list) -> None:
        """Multi-line comments don't nest (/* in comment is ignored)."""
        # /* not /* nested */ - the inner /* is just part of the comment
        result = loads_relaxed('{"a": /* not /* nested */ 1}', repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1


class TestHashComments:
    """Test hash # comments."""

    def test_hash_comment_end(self, repair_log: list) -> None:
        """Hash comment at end of JSON."""
        result = loads_relaxed('{"a": 1} # comment', repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1
        assert repair_log[0].kind == RepairKind.HASH_COMMENT

    def test_hash_comment_own_line(self, repair_log: list) -> None:
        """Hash comment on its own line."""
        result = loads_relaxed('# comment\n{"a": 1}', repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1

    def test_hash_comment_between(self, repair_log: list) -> None:
        """Hash comment between properties."""
        result = loads_relaxed('{"a": 1, # comment\n"b": 2}', repair_log=repair_log)
        assert result == {"a": 1, "b": 2}
        assert len(repair_log) == 1


class TestCommentsInStrings:
    """Test that comment-like patterns in strings are preserved."""

    def test_double_slash_in_string(self, repair_log: list) -> None:
        """URL with // in string is preserved."""
        result = loads_relaxed('{"url": "http://example.com"}', repair_log=repair_log)
        assert result == {"url": "http://example.com"}
        assert repair_log == []

    def test_slash_star_in_string(self, repair_log: list) -> None:
        """/* in string is preserved."""
        result = loads_relaxed(
            '{"text": "/* not a comment */"}', repair_log=repair_log
        )
        assert result == {"text": "/* not a comment */"}
        assert repair_log == []

    def test_hash_in_string(self, repair_log: list) -> None:
        """# in string is preserved."""
        result = loads_relaxed('{"tag": "#hashtag"}', repair_log=repair_log)
        assert result == {"tag": "#hashtag"}
        assert repair_log == []

    def test_complex_url_in_string(self, repair_log: list) -> None:
        """Complex URL with // preserved."""
        result = loads_relaxed(
            '{"url": "https://example.com/path?q=1#anchor"}', repair_log=repair_log
        )
        assert result == {"url": "https://example.com/path?q=1#anchor"}
        assert repair_log == []


class TestCommentEdgeCases:
    """Test edge cases for comments."""

    def test_comment_only_whitespace(self, repair_log: list) -> None:
        """Comment containing only whitespace."""
        result = loads_relaxed('// \n{"a": 1}', repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1

    def test_empty_comment(self, repair_log: list) -> None:
        """Empty multi-line comment."""
        result = loads_relaxed('/**/ {"a": 1}', repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1

    def test_comment_with_special_chars(self, repair_log: list) -> None:
        """Comment with unicode and special characters."""
        result = loads_relaxed('// 日本語 émoji 🎉\n{"a": 1}', repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1

    def test_unclosed_multiline_comment_error(self) -> None:
        """Unclosed multi-line comment should error."""
        with pytest.raises((json.JSONDecodeError, ValueError)):
            loads_relaxed('/* unclosed {"a": 1}')

    def test_comment_at_eof_no_newline(self, repair_log: list) -> None:
        """Comment at end of file without newline."""
        result = loads_relaxed('{"a": 1}// comment', repair_log=repair_log)
        assert result == {"a": 1}
        assert len(repair_log) == 1


class TestRepairLog:
    """Test repair log accuracy for comments."""

    def test_comment_repair_log_position(self, repair_log: list) -> None:
        """Repair log records correct position for comment."""
        loads_relaxed('{"a": 1} // comment', repair_log=repair_log)
        repair = repair_log[0]
        assert repair.position == 9  # Position of //
        assert repair.line == 1

    def test_comment_repair_includes_content(self, repair_log: list) -> None:
        """Repair includes original comment content."""
        loads_relaxed('{"a": 1} /* my comment */', repair_log=repair_log)
        repair = repair_log[0]
        assert "my comment" in repair.original


class TestStrictMode:
    """Test strict mode rejects comments."""

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


class TestDisabledOption:
    """Test with allow_comments=False."""

    def test_disabled_rejects_comments(self) -> None:
        """Disabling comments option causes error."""
        with pytest.raises(json.JSONDecodeError):
            loads_relaxed('{"a": 1} // comment', allow_comments=False)

    def test_disabled_allows_other_relaxations(self, repair_log: list) -> None:
        """Other relaxations still work when comments are disabled."""
        result = loads_relaxed(
            '{"a": 1,}',
            allow_comments=False,
            repair_log=repair_log,
        )
        assert result == {"a": 1}
        assert len(repair_log) == 1  # Trailing comma removal only
