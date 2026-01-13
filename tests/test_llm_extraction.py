"""Tests for LLM-specific JSON error handling.

These tests define the expected behavior for extracting and repairing
JSON from LLM responses. Tests are written before implementation (TDD).

Phase 1 Features:
- JSON extraction from text with preamble/postamble
- Markdown code fence removal
- Unescaped quote repair inside strings
"""

from __future__ import annotations

import pytest

from jsonfix import loads_relaxed, RepairKind


class TestJSONExtraction:
    """Test extraction of JSON from LLM responses with surrounding text."""

    # === Preamble Tests ===

    def test_simple_preamble(self, repair_log: list) -> None:
        """Extract JSON after simple preamble text."""
        text = 'Here is the JSON: {"name": "test"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"name": "test"}
        assert any(r.kind == RepairKind.JSON_EXTRACTED for r in repair_log)

    def test_preamble_with_newline(self, repair_log: list) -> None:
        """Extract JSON after preamble with newline."""
        text = 'Here is the JSON:\n{"name": "test"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"name": "test"}

    def test_preamble_with_colon(self, repair_log: list) -> None:
        """Handle preamble ending with colon."""
        text = 'The result is: {"value": 42}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"value": 42}

    def test_preamble_multiline(self, repair_log: list) -> None:
        """Handle multi-line preamble."""
        text = 'Based on your request,\nI have created:\n{"data": []}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"data": []}

    def test_preamble_with_quotes(self, repair_log: list) -> None:
        """Handle preamble containing quotes."""
        text = 'Here\'s the "output" you wanted: {"a": 1}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_preamble_claude_style(self, repair_log: list) -> None:
        """Handle typical Claude preamble."""
        text = 'Here\'s the analysis in JSON format:\n\n{"score": 85}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"score": 85}

    def test_preamble_chatgpt_style(self, repair_log: list) -> None:
        """Handle typical ChatGPT preamble."""
        text = 'Based on your request, here is the structured data:\n{"status": "success"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"status": "success"}

    # === Postamble Tests ===

    def test_simple_postamble(self, repair_log: list) -> None:
        """Extract JSON before postamble text."""
        text = '{"name": "test"} Let me know if you need changes.'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"name": "test"}

    def test_postamble_with_newline(self, repair_log: list) -> None:
        """Extract JSON before postamble with newline."""
        text = '{"name": "test"}\nHope this helps!'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"name": "test"}

    def test_postamble_question(self, repair_log: list) -> None:
        """Handle postamble with question."""
        text = '{"result": true} Is this what you wanted?'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"result": True}

    def test_postamble_multiline(self, repair_log: list) -> None:
        """Handle multi-line postamble."""
        text = '{"data": [1, 2, 3]}\n\nLet me know if you need any changes.\nI can modify the format.'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"data": [1, 2, 3]}

    # === Combined Preamble + Postamble ===

    def test_preamble_and_postamble(self, repair_log: list) -> None:
        """Extract JSON with both preamble and postamble."""
        text = 'Here you go: {"a": 1} Let me know!'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_complex_wrapper(self, repair_log: list) -> None:
        """Handle complex surrounding text."""
        text = """Based on the analysis of your data,
here is the structured output:
{"score": 85, "grade": "B"}
Feel free to ask if you need clarification!"""
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"score": 85, "grade": "B"}

    def test_full_llm_response(self, repair_log: list) -> None:
        """Handle a realistic full LLM response."""
        text = """I've analyzed the document and extracted the key information.

{"title": "Q4 Report", "metrics": {"revenue": 1500000, "growth": 0.15}}

This JSON contains the main metrics from the report. The revenue figure represents the total for Q4, and the growth rate is compared to the previous quarter.

Would you like me to extract any additional information?"""
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"title": "Q4 Report", "metrics": {"revenue": 1500000, "growth": 0.15}}

    # === Array Extraction ===

    def test_extract_array(self, repair_log: list) -> None:
        """Extract array from text."""
        text = 'The items are: [1, 2, 3]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [1, 2, 3]

    def test_extract_array_of_objects(self, repair_log: list) -> None:
        """Extract array of objects from text."""
        text = 'Users: [{"name": "Alice"}, {"name": "Bob"}] Done.'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [{"name": "Alice"}, {"name": "Bob"}]

    def test_extract_array_with_postamble(self, repair_log: list) -> None:
        """Extract array with postamble."""
        text = '[1, 2, 3, 4, 5]\n\nThese are the first five integers.'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [1, 2, 3, 4, 5]

    # === Nested JSON ===

    def test_nested_json_extraction(self, repair_log: list) -> None:
        """Correctly find matching brackets in nested JSON."""
        text = 'Result: {"outer": {"inner": {"deep": 1}}} End'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"outer": {"inner": {"deep": 1}}}

    def test_mixed_brackets(self, repair_log: list) -> None:
        """Handle mixed arrays and objects."""
        text = 'Data: {"items": [1, [2, 3], {"x": 4}]} Done'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"items": [1, [2, 3], {"x": 4}]}

    def test_deeply_nested(self, repair_log: list) -> None:
        """Handle deeply nested structures."""
        text = 'Output: {"a": {"b": {"c": {"d": {"e": 5}}}}} finished'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": {"b": {"c": {"d": {"e": 5}}}}}

    # === Edge Cases ===

    def test_no_extraction_needed(self, repair_log: list) -> None:
        """Pure JSON should pass through unchanged."""
        text = '{"name": "test"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"name": "test"}
        # Should NOT log JSON_EXTRACTED when no extraction was needed
        assert not any(r.kind == RepairKind.JSON_EXTRACTED for r in repair_log)

    def test_json_with_string_containing_braces(self, repair_log: list) -> None:
        """Don't be fooled by braces in strings."""
        text = 'Output: {"code": "if (x) { return y; }"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"code": "if (x) { return y; }"}

    def test_json_with_string_containing_brackets(self, repair_log: list) -> None:
        """Don't be fooled by brackets in strings."""
        text = 'Result: {"array_str": "[1, 2, 3]"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"array_str": "[1, 2, 3]"}

    def test_multiple_json_objects_takes_first(self, repair_log: list) -> None:
        """When multiple JSON objects exist, extract first complete one."""
        text = 'First: {"a": 1} Second: {"b": 2}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_empty_preamble_only_whitespace(self, repair_log: list) -> None:
        """Handle whitespace-only preamble."""
        text = '   \n  {"a": 1}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_empty_postamble_only_whitespace(self, repair_log: list) -> None:
        """Handle whitespace-only postamble."""
        text = '{"a": 1}   \n  '
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    # === Repair Logging ===

    def test_extraction_logs_repair(self, repair_log: list) -> None:
        """Verify repair is logged with correct details."""
        text = 'Here: {"a": 1}'
        loads_relaxed(text, repair_log=repair_log)

        extraction_repairs = [r for r in repair_log if r.kind == RepairKind.JSON_EXTRACTED]
        assert len(extraction_repairs) == 1
        repair = extraction_repairs[0]
        assert "Here:" in repair.original or repair.original == "Here: "
        assert repair.line == 1
        assert repair.column == 1

    def test_extraction_logs_postamble(self, repair_log: list) -> None:
        """Verify postamble is recorded in repair."""
        text = '{"a": 1} trailing text'
        loads_relaxed(text, repair_log=repair_log)

        extraction_repairs = [r for r in repair_log if r.kind == RepairKind.JSON_EXTRACTED]
        assert len(extraction_repairs) == 1


class TestMarkdownFences:
    """Test removal of markdown code fences around JSON."""

    # === Basic Fence Removal ===

    def test_json_fence(self, repair_log: list) -> None:
        """Remove ```json fence."""
        text = '```json\n{"a": 1}\n```'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}
        assert any(r.kind == RepairKind.MARKDOWN_FENCE_REMOVED for r in repair_log)

    def test_plain_fence(self, repair_log: list) -> None:
        """Remove plain ``` fence without language."""
        text = '```\n{"a": 1}\n```'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_javascript_fence(self, repair_log: list) -> None:
        """Remove ```javascript fence."""
        text = '```javascript\n{"a": 1}\n```'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_js_fence(self, repair_log: list) -> None:
        """Remove ```js fence."""
        text = '```js\n{"a": 1}\n```'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_jsonc_fence(self, repair_log: list) -> None:
        """Remove ```jsonc fence (JSON with comments)."""
        text = '```jsonc\n{"a": 1}\n```'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    # === Fence Variations ===

    def test_fence_with_spaces(self, repair_log: list) -> None:
        """Handle spaces in fence."""
        text = '``` json\n{"a": 1}\n```'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_fence_case_insensitive(self, repair_log: list) -> None:
        """Handle different cases."""
        text = '```JSON\n{"a": 1}\n```'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_fence_with_extra_newlines(self, repair_log: list) -> None:
        """Handle extra newlines."""
        text = '```json\n\n{"a": 1}\n\n```'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_fence_no_trailing_newline(self, repair_log: list) -> None:
        """Handle missing newline before closing fence."""
        text = '```json\n{"a": 1}```'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_fence_windows_line_endings(self, repair_log: list) -> None:
        """Handle Windows line endings."""
        text = '```json\r\n{"a": 1}\r\n```'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    # === Combined with Preamble/Postamble ===

    def test_fence_with_preamble(self, repair_log: list) -> None:
        """Handle preamble before fence."""
        text = 'Here is the code:\n```json\n{"a": 1}\n```'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_fence_with_postamble(self, repair_log: list) -> None:
        """Handle postamble after fence."""
        text = '```json\n{"a": 1}\n```\nLet me know!'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_fence_with_both(self, repair_log: list) -> None:
        """Handle both preamble and postamble."""
        text = 'Result:\n```json\n{"a": 1}\n```\nDone!'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_fence_full_llm_response(self, repair_log: list) -> None:
        """Handle realistic LLM response with fenced JSON."""
        text = """Here's the configuration you requested:

```json
{
    "name": "my-app",
    "version": "1.0.0",
    "dependencies": {}
}
```

You can save this as package.json in your project root."""
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"name": "my-app", "version": "1.0.0", "dependencies": {}}

    # === Array in Fence ===

    def test_fence_with_array(self, repair_log: list) -> None:
        """Handle array in fence."""
        text = '```json\n[1, 2, 3]\n```'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == [1, 2, 3]

    # === Edge Cases ===

    def test_fence_in_string_not_removed(self, repair_log: list) -> None:
        """Don't remove fences that are part of string content."""
        # Disable smart quote normalization since ` is converted to ' by that feature
        text = '{"markdown": "Use ```code``` for code blocks"}'
        result = loads_relaxed(text, repair_log=repair_log, normalize_quotes=False)
        assert result == {"markdown": "Use ```code``` for code blocks"}
        # Should NOT have MARKDOWN_FENCE_REMOVED
        assert not any(r.kind == RepairKind.MARKDOWN_FENCE_REMOVED for r in repair_log)

    def test_unclosed_fence(self, repair_log: list) -> None:
        """Handle unclosed fence gracefully."""
        text = '```json\n{"a": 1}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_multiple_fences_first_only(self, repair_log: list) -> None:
        """Multiple fenced blocks - extract first."""
        text = '```json\n{"a": 1}\n```\n\n```json\n{"b": 2}\n```'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    def test_no_fence_passthrough(self, repair_log: list) -> None:
        """JSON without fence passes through."""
        text = '{"a": 1}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}
        # Should NOT have MARKDOWN_FENCE_REMOVED
        assert not any(r.kind == RepairKind.MARKDOWN_FENCE_REMOVED for r in repair_log)

    def test_fence_only_opening(self, repair_log: list) -> None:
        """Handle only opening fence without closing."""
        text = '```\n{"a": 1}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1}

    # === Repair Logging ===

    def test_fence_removal_logs_repair(self, repair_log: list) -> None:
        """Verify fence removal is logged correctly."""
        text = '```json\n{"a": 1}\n```'
        loads_relaxed(text, repair_log=repair_log)

        fence_repairs = [r for r in repair_log if r.kind == RepairKind.MARKDOWN_FENCE_REMOVED]
        assert len(fence_repairs) >= 1


class TestUnescapedQuotes:
    """Test repair of unescaped quotes inside JSON strings."""

    # === Simple Cases ===

    def test_single_unescaped_quote(self, repair_log: list) -> None:
        """Fix single unescaped quote in string."""
        text = '{"text": "He said "hello" today"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": 'He said "hello" today'}
        assert any(r.kind == RepairKind.UNESCAPED_QUOTE for r in repair_log)

    def test_multiple_unescaped_quotes(self, repair_log: list) -> None:
        """Fix multiple unescaped quotes."""
        text = '{"text": "She said "yes" and "no""}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": 'She said "yes" and "no"'}

    def test_quote_at_start_of_value(self, repair_log: list) -> None:
        """Fix quote at start of string value."""
        text = '{"text": ""Hello" is a greeting"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": '"Hello" is a greeting'}

    def test_quote_at_end_of_value(self, repair_log: list) -> None:
        """Fix quote at end of string value."""
        text = '{"text": "The word is "hello""}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": 'The word is "hello"'}

    # === Complex Patterns ===

    def test_nested_quoted_phrase(self, repair_log: list) -> None:
        """Fix deeply nested quoted phrase."""
        text = '{"article": "The article titled "AI Today" discusses "machine learning""}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"article": 'The article titled "AI Today" discusses "machine learning"'}

    def test_quote_followed_by_punctuation(self, repair_log: list) -> None:
        """Handle quote followed by punctuation."""
        text = '{"text": "She said "wow!", then left"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": 'She said "wow!", then left'}

    def test_quote_with_colon_inside(self, repair_log: list) -> None:
        """Don't confuse quoted text containing colon."""
        text = '{"note": "See "Part 1: Introduction" for details"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"note": 'See "Part 1: Introduction" for details'}

    def test_quote_with_comma_inside(self, repair_log: list) -> None:
        """Handle quoted text containing comma."""
        text = '{"text": "The terms "A, B, and C" are important"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": 'The terms "A, B, and C" are important'}

    # === Already Escaped (No Change) ===

    def test_already_escaped_unchanged(self, repair_log: list) -> None:
        """Already escaped quotes should not be double-escaped."""
        text = '{"text": "He said \\"hello\\""}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": 'He said "hello"'}
        # Should NOT have UNESCAPED_QUOTE for already escaped
        assert not any(r.kind == RepairKind.UNESCAPED_QUOTE for r in repair_log)

    def test_mixed_escaped_unescaped(self, repair_log: list) -> None:
        """Handle mix of escaped and unescaped."""
        text = '{"text": "First \\"ok\\" then "not ok""}'
        result = loads_relaxed(text, repair_log=repair_log)
        # First quote pair is already escaped, second needs escaping
        assert result == {"text": 'First "ok" then "not ok"'}

    def test_unescaped_quote_with_escapes_in_following_text(
        self, repair_log: list
    ) -> None:
        """Handle unescaped quote followed by text with escape sequences.

        This tests the escape sequence handling during quote look-ahead.
        """
        text = '{"text": "He said "hi\\nthere" today"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": 'He said "hi\nthere" today'}

    def test_unescaped_quote_before_escaped_string_value(
        self, repair_log: list
    ) -> None:
        """Handle unescaped quote immediately before another string with escapes.

        This tests when a quote is followed directly by another quoted value
        that contains escape sequences (hitting the lookahead escape handling).
        """
        # This creates: {"items": ["first" "path\\to\\file"]}
        # The unescaped quote after "first" is followed by a string with escapes
        text = '{"items": ["first" "path\\\\to\\\\file"]}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"items": ["first", "path\\to\\file"]}

    def test_unescaped_quote_in_object_with_following_key(
        self, repair_log: list
    ) -> None:
        """Handle unescaped quote in object context with comma and next key.

        This tests the in_object context detection when a quoted value
        with unescaped quotes is followed by another key-value pair.
        """
        text = '{"a": "text "nested"", "b": 1}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 'text "nested"', "b": 1}

    # === Array Values ===

    def test_unescaped_in_array(self, repair_log: list) -> None:
        """Fix unescaped quotes in array strings."""
        text = '["He said "hi"", "She said "bye""]'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == ['He said "hi"', 'She said "bye"']

    def test_unescaped_in_nested_array(self, repair_log: list) -> None:
        """Fix unescaped quotes in nested array."""
        text = '{"items": ["Quote "one"", "Quote "two""]}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"items": ['Quote "one"', 'Quote "two"']}

    # === Heuristic Edge Cases ===

    def test_empty_quoted_phrase(self, repair_log: list) -> None:
        """Handle empty quotes."""
        text = '{"text": "The value is """}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": 'The value is ""'}

    def test_single_word_quoted(self, repair_log: list) -> None:
        """Single word in quotes."""
        text = '{"word": "The "important" word"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"word": 'The "important" word'}

    def test_number_after_quote(self, repair_log: list) -> None:
        """Quote followed by number."""
        text = '{"text": "Version "2.0" released"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": 'Version "2.0" released'}

    def test_quoted_url(self, repair_log: list) -> None:
        """Handle quoted URL in text."""
        text = '{"note": "Visit "https://example.com" for info"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"note": 'Visit "https://example.com" for info'}

    # === Multiple Values ===

    def test_multiple_keys_with_unescaped(self, repair_log: list) -> None:
        """Fix unescaped quotes across multiple keys."""
        text = '{"a": "Said "hi"", "b": "Said "bye""}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 'Said "hi"', "b": 'Said "bye"'}

    # === No False Positives ===

    def test_valid_json_unchanged(self, repair_log: list) -> None:
        """Valid JSON should not be modified."""
        text = '{"text": "normal text without inner quotes"}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": "normal text without inner quotes"}
        assert not any(r.kind == RepairKind.UNESCAPED_QUOTE for r in repair_log)

    def test_properly_escaped_json(self, repair_log: list) -> None:
        """Properly escaped JSON should not be modified."""
        text = '{"text": "He said \\"hello\\" and \\"goodbye\\""}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": 'He said "hello" and "goodbye"'}
        assert not any(r.kind == RepairKind.UNESCAPED_QUOTE for r in repair_log)

    def test_empty_string_unchanged(self, repair_log: list) -> None:
        """Empty string should not be affected."""
        text = '{"text": ""}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": ""}
        assert not any(r.kind == RepairKind.UNESCAPED_QUOTE for r in repair_log)

    # === LLM Realistic Cases ===

    def test_llm_article_summary(self, repair_log: list) -> None:
        """Handle LLM article summary with quotes."""
        text = '''{"summary": "The article "Understanding AI" by Smith discusses how "machine learning" is transforming industries."}'''
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"summary": 'The article "Understanding AI" by Smith discusses how "machine learning" is transforming industries.'}

    def test_llm_code_explanation(self, repair_log: list) -> None:
        """Handle LLM code explanation with quotes."""
        text = '{"explanation": "The function "calculateTotal" returns the sum of all "items" in the array."}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"explanation": 'The function "calculateTotal" returns the sum of all "items" in the array.'}

    # === Repair Logging ===

    def test_unescaped_quote_logs_repair(self, repair_log: list) -> None:
        """Verify unescaped quote repair is logged."""
        text = '{"text": "He said "hello""}'
        loads_relaxed(text, repair_log=repair_log)

        quote_repairs = [r for r in repair_log if r.kind == RepairKind.UNESCAPED_QUOTE]
        assert len(quote_repairs) >= 1

    def test_multiple_repairs_logged(self, repair_log: list) -> None:
        """Verify multiple unescaped quotes are logged."""
        text = '{"text": "Quote "A" and "B" and "C""}'
        loads_relaxed(text, repair_log=repair_log)

        quote_repairs = [r for r in repair_log if r.kind == RepairKind.UNESCAPED_QUOTE]
        # Should log multiple repairs for multiple unescaped quote pairs
        assert len(quote_repairs) >= 3


class TestCombinedLLMFeatures:
    """Test combinations of LLM extraction features."""

    def test_fence_with_trailing_comma(self, repair_log: list) -> None:
        """Handle fenced JSON with trailing comma."""
        text = '```json\n{"a": 1, "b": 2,}\n```'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}

    def test_extraction_with_comments(self, repair_log: list) -> None:
        """Handle extracted JSON with comments."""
        text = 'Here is the config:\n{"a": 1, // comment\n"b": 2}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"a": 1, "b": 2}

    def test_fence_with_python_literals(self, repair_log: list) -> None:
        """Handle fenced JSON with Python literals."""
        text = '```json\n{"active": True, "data": None}\n```'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"active": True, "data": None}

    def test_extraction_with_unescaped_quotes(self, repair_log: list) -> None:
        """Handle extraction and unescaped quotes together."""
        text = 'Result: {"text": "He said "hello""}'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": 'He said "hello"'}

    def test_fence_with_unescaped_quotes(self, repair_log: list) -> None:
        """Handle fenced JSON with unescaped quotes."""
        text = '```json\n{"text": "She said "yes""}\n```'
        result = loads_relaxed(text, repair_log=repair_log)
        assert result == {"text": 'She said "yes"'}

    def test_full_llm_response_all_features(self, repair_log: list) -> None:
        """Handle LLM response using all Phase 1 features."""
        text = """Based on my analysis, here's the result:

```json
{
    "title": "Analysis of "Important Data"",
    "findings": [
        {"item": "Finding "A"", "status": True,},
        {"item": "Finding "B"", "status": False,},
    ],
    // Additional metadata
    "timestamp": None,
}
```

Let me know if you need any clarification!"""
        result = loads_relaxed(text, repair_log=repair_log)

        assert result["title"] == 'Analysis of "Important Data"'
        assert len(result["findings"]) == 2
        assert result["findings"][0]["status"] is True
        assert result["timestamp"] is None

    def test_feature_disable_extraction(self, repair_log: list) -> None:
        """Verify extraction can be disabled."""
        text = 'Prefix: {"a": 1}'
        # When extraction is disabled, this should fail to parse
        with pytest.raises(Exception):  # JSONDecodeError
            loads_relaxed(text, extract_json=False, repair_log=repair_log)

    def test_feature_disable_fence_removal(self, repair_log: list) -> None:
        """Verify fence removal can be disabled."""
        text = '```json\n{"a": 1}\n```'
        # When fence removal AND extraction are disabled, this should fail to parse
        # Also disable smart quotes (` -> ') and single quotes to prevent accidental parsing
        with pytest.raises(Exception):  # JSONDecodeError
            loads_relaxed(
                text,
                remove_markdown_fences=False,
                extract_json=False,
                normalize_quotes=False,
                allow_single_quote_strings=False,
                repair_log=repair_log
            )
