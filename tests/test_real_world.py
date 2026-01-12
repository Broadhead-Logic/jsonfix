"""Tests for real-world examples."""

from __future__ import annotations

import pytest

from jsonfix import loads_relaxed, RepairKind


class TestLLMOutputExamples:
    """Test typical LLM output patterns."""

    @pytest.mark.real_world
    def test_chatgpt_response_with_trailing_comma(self, repair_log: list) -> None:
        """Typical ChatGPT JSON response with trailing comma."""
        json_str = """{
            "response": "Here is the data you requested",
            "items": ["apple", "banana", "cherry",],
            "metadata": {
                "count": 3,
                "source": "database",
            },
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["response"] == "Here is the data you requested"
        assert result["items"] == ["apple", "banana", "cherry"]
        assert result["metadata"]["count"] == 3
        # Multiple trailing commas
        trailing = [r for r in repair_log if r.kind == RepairKind.TRAILING_COMMA]
        assert len(trailing) >= 3

    @pytest.mark.real_world
    def test_llm_with_smart_quotes(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """LLM output that was copied through a word processor."""
        left = smart_double_quotes["left"]
        right = smart_double_quotes["right"]
        json_str = f'{{{left}message{right}: {left}Hello world{right}}}'
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["message"] == "Hello world"
        quote_repairs = [r for r in repair_log if r.kind == RepairKind.SMART_QUOTE]
        assert len(quote_repairs) == 4

    @pytest.mark.real_world
    def test_llm_function_call_response(self, repair_log: list) -> None:
        """LLM function calling response format."""
        json_str = """{
            "name": "get_weather",
            "arguments": {
                "location": "San Francisco",
                "unit": "celsius",
            },
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["name"] == "get_weather"
        assert result["arguments"]["location"] == "San Francisco"


class TestConfigFileExamples:
    """Test config file patterns (JSONC-style)."""

    @pytest.mark.real_world
    def test_vscode_settings_style(self, repair_log: list) -> None:
        """VS Code settings.json style."""
        json_str = """{
            // Editor settings
            "editor.fontSize": 14,
            "editor.tabSize": 2,
            "editor.wordWrap": "on",

            // Terminal settings
            "terminal.integrated.fontSize": 13,

            // Extensions
            "extensions.autoUpdate": true,
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["editor.fontSize"] == 14
        assert result["editor.tabSize"] == 2
        assert result["terminal.integrated.fontSize"] == 13
        assert result["extensions.autoUpdate"] is True

    @pytest.mark.real_world
    def test_tsconfig_style(self, repair_log: list) -> None:
        """tsconfig.json style."""
        json_str = """{
            "compilerOptions": {
                "target": "ES2020",
                "module": "commonjs",
                /* Strict type checking */
                "strict": true,
                "esModuleInterop": true,
                "skipLibCheck": true,
                "forceConsistentCasingInFileNames": true,
            },
            "include": ["src/**/*",],
            "exclude": ["node_modules",],
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["compilerOptions"]["target"] == "ES2020"
        assert result["compilerOptions"]["strict"] is True
        assert "src/**/*" in result["include"]

    @pytest.mark.real_world
    def test_eslint_config_style(self, repair_log: list) -> None:
        """ESLint configuration style."""
        json_str = """{
            "env": {
                "browser": true,
                "es2021": true,
            },
            "extends": [
                "eslint:recommended",
                // "plugin:react/recommended",
            ],
            "rules": {
                "indent": ["error", 2,],
                "linebreak-style": ["error", "unix",],
                "quotes": ["error", "single",],
                "semi": ["error", "always",],
            },
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["env"]["browser"] is True
        assert "eslint:recommended" in result["extends"]


class TestDashboardExamples:
    """Test dashboard/API response patterns."""

    @pytest.mark.real_world
    def test_api_response_with_comments(self, repair_log: list) -> None:
        """API response that was annotated with comments."""
        json_str = """// API Response from /api/users
        {
            "status": "ok",
            "data": [
                {"id": 1, "name": "Alice",},
                {"id": 2, "name": "Bob",},
            ],
            "pagination": {
                "page": 1,
                "total": 2,
            },
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["status"] == "ok"
        assert len(result["data"]) == 2
        assert result["data"][0]["name"] == "Alice"

    @pytest.mark.real_world
    def test_metrics_dashboard_export(self, repair_log: list) -> None:
        """Metrics dashboard export."""
        json_str = """{
            "dashboard": "System Metrics",
            "timestamp": "2025-01-12T10:30:00Z",
            "metrics": {
                "cpu_percent": 45.5,
                "memory_percent": 72.3,
                "disk_percent": 89.1,
                "network_in_mbps": 125.4,
                "network_out_mbps": 87.2,
            },
            "alerts": [
                {"level": "warning", "message": "High disk usage",},
            ],
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["dashboard"] == "System Metrics"
        assert result["metrics"]["cpu_percent"] == 45.5
        assert result["alerts"][0]["level"] == "warning"


class TestDocumentationExamples:
    """Test JSON from documentation."""

    @pytest.mark.real_world
    def test_markdown_json_block(self, repair_log: list) -> None:
        """JSON that might be pasted from markdown docs."""
        # Often has trailing commas in documentation for readability
        json_str = """{
            "name": "my-package",
            "version": "1.0.0",
            "dependencies": {
                "lodash": "^4.17.21",
                "axios": "^1.6.0",
            },
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["name"] == "my-package"
        assert result["version"] == "1.0.0"

    @pytest.mark.real_world
    def test_tutorial_example(self, repair_log: list) -> None:
        """JSON from a tutorial with comments explaining structure."""
        json_str = """{
            // User object schema
            "user": {
                "id": 123,           // Unique identifier
                "name": "John Doe",  // Full name
                "email": "john@example.com",
                "roles": [
                    "admin",
                    "editor",  // Can edit content
                ],
            },
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["user"]["id"] == 123
        assert "admin" in result["user"]["roles"]


class TestCopyPasteIssues:
    """Test common copy-paste issues."""

    @pytest.mark.real_world
    def test_word_processor_quotes(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """JSON pasted from Word or Google Docs with smart quotes."""
        left = smart_double_quotes["left"]
        right = smart_double_quotes["right"]
        json_str = f"""{{
            {left}title{right}: {left}My Document{right},
            {left}author{right}: {left}John Doe{right},
            {left}pages{right}: 42
        }}"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["title"] == "My Document"
        assert result["author"] == "John Doe"
        assert result["pages"] == 42

    @pytest.mark.real_world
    def test_slack_message_json(self, repair_log: list) -> None:
        """JSON that was shared in a Slack message."""
        # Slack sometimes converts quotes
        json_str = """{
            "channel": "#general",
            "message": "Hello team!",
            "attachments": [
                {
                    "title": "Report",
                    "url": "https://example.com/report",
                },
            ],
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["channel"] == "#general"
        assert result["attachments"][0]["title"] == "Report"

    @pytest.mark.real_world
    def test_email_json(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """JSON from an email (often has smart quotes from email clients)."""
        left = smart_double_quotes["left"]
        right = smart_double_quotes["right"]
        json_str = f"""{{
            {left}subject{right}: {left}Meeting Notes{right},
            {left}date{right}: {left}2025-01-12{right},
            {left}attendees{right}: [{left}Alice{right}, {left}Bob{right}]
        }}"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["subject"] == "Meeting Notes"
        assert "Alice" in result["attendees"]


class TestMixedRealWorldScenarios:
    """Test mixed real-world scenarios."""

    @pytest.mark.real_world
    def test_llm_config_generation(self, repair_log: list) -> None:
        """LLM generating a config file with comments."""
        json_str = """{
            // Generated by AI Assistant
            "app_name": "MyApp",
            "version": "2.0.0",

            /* Database configuration */
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "myapp_db",
            },

            // Feature flags
            "features": {
                "dark_mode": true,
                "beta_features": false,
            },
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["app_name"] == "MyApp"
        assert result["database"]["port"] == 5432
        assert result["features"]["dark_mode"] is True
        # Should have various repair types
        kinds = {r.kind for r in repair_log}
        assert RepairKind.SINGLE_LINE_COMMENT in kinds
        assert RepairKind.MULTI_LINE_COMMENT in kinds
        assert RepairKind.TRAILING_COMMA in kinds

    @pytest.mark.real_world
    def test_debugging_json_with_annotations(self, repair_log: list) -> None:
        """JSON being debugged with inline annotations."""
        json_str = """{
            "request_id": "abc123",  // TODO: make this UUID
            "status": "pending",     # needs review
            "data": {
                /* raw response from API */
                "items": [1, 2, 3,],
                "next_cursor": null,
            },
        }"""
        result = loads_relaxed(json_str, repair_log=repair_log)
        assert result["request_id"] == "abc123"
        assert result["data"]["items"] == [1, 2, 3]
        # Should have all comment types
        comment_kinds = {
            r.kind
            for r in repair_log
            if "COMMENT" in r.kind.name
        }
        assert len(comment_kinds) >= 2  # At least 2 different comment types
