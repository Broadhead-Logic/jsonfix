"""Tests with complex, long JSON documents containing multiple error types."""

from __future__ import annotations

import pytest

from jsonfix import loads_relaxed, RepairKind


class TestComplexConfigFiles:
    """Test large config files with multiple error types."""

    def test_vscode_settings_full(self, repair_log: list) -> None:
        """Full VS Code settings.json with 20+ errors."""
        json_str = """{
            // ===========================================
            // Editor Configuration
            // ===========================================

            /* Font and display settings */
            "editor.fontSize": 14,
            "editor.fontFamily": "Fira Code, Consolas, monospace",
            "editor.fontLigatures": true,
            "editor.lineHeight": 1.6,
            "editor.letterSpacing": 0.5,

            // Tab and indentation
            "editor.tabSize": 4,
            "editor.insertSpaces": true,
            "editor.detectIndentation": true,
            "editor.autoIndent": "full",

            /* Word wrap configuration */
            "editor.wordWrap": "on",
            "editor.wordWrapColumn": 120,
            "editor.wrappingIndent": "indent",

            // Cursor and selection
            "editor.cursorStyle": "line",
            "editor.cursorBlinking": "smooth",
            "editor.cursorSmoothCaretAnimation": "on",
            "editor.multiCursorModifier": "ctrlCmd",

            // ===========================================
            // Formatting
            // ===========================================

            "editor.formatOnSave": true,
            "editor.formatOnPaste": true,
            "editor.formatOnType": false,
            "editor.defaultFormatter": "esbenp.prettier-vscode",

            /* Auto-save configuration */
            "files.autoSave": "afterDelay",
            "files.autoSaveDelay": 1000,

            // ===========================================
            // Terminal Settings
            // ===========================================

            "terminal.integrated.fontSize": 13,
            "terminal.integrated.fontFamily": "Fira Code",
            "terminal.integrated.lineHeight": 1.4,
            "terminal.integrated.cursorStyle": "line",
            "terminal.integrated.cursorBlinking": true,

            # Python-specific settings (hash comment)
            "python.linting.enabled": true,
            "python.linting.pylintEnabled": true,
            "python.formatting.provider": "black",

            // ===========================================
            // Git Configuration
            // ===========================================

            "git.enableSmartCommit": true,
            "git.autofetch": true,
            "git.confirmSync": false,
            "git.defaultCloneDirectory": "~/projects",

            /* Diff editor settings */
            "diffEditor.ignoreTrimWhitespace": false,
            "diffEditor.renderSideBySide": true,

            // ===========================================
            // Workbench
            // ===========================================

            "workbench.colorTheme": "One Dark Pro",
            "workbench.iconTheme": "material-icon-theme",
            "workbench.startupEditor": "newUntitledFile",
            "workbench.editor.enablePreview": false,
            "workbench.editor.showTabs": true,

            // Sidebar and panel
            "workbench.sideBar.location": "left",
            "workbench.panel.defaultLocation": "bottom",
            "workbench.activityBar.visible": true,
            "workbench.statusBar.visible": true,
        }"""

        result = loads_relaxed(json_str, repair_log=repair_log)

        # Verify structure
        assert result["editor.fontSize"] == 14
        assert result["terminal.integrated.fontSize"] == 13
        assert result["workbench.colorTheme"] == "One Dark Pro"

        # Verify we have many repairs (comments + trailing commas)
        assert len(repair_log) >= 20

        # Verify multiple repair kinds
        kinds = {r.kind for r in repair_log}
        assert RepairKind.SINGLE_LINE_COMMENT in kinds
        assert RepairKind.MULTI_LINE_COMMENT in kinds
        assert RepairKind.HASH_COMMENT in kinds
        assert RepairKind.TRAILING_COMMA in kinds

    def test_eslint_config_complex(self, repair_log: list) -> None:
        """Complex ESLint config with nested rules."""
        json_str = """{
            // ESLint Configuration
            "env": {
                "browser": true,
                "es2021": true,
                "node": true,
                "jest": true,
            },

            "extends": [
                "eslint:recommended",
                "plugin:react/recommended",
                "plugin:@typescript-eslint/recommended",
                "prettier",
            ],

            "parser": "@typescript-eslint/parser",

            "parserOptions": {
                "ecmaVersion": "latest",
                "sourceType": "module",
                "ecmaFeatures": {
                    "jsx": true,
                },
            },

            "plugins": [
                "react",
                "react-hooks",
                "@typescript-eslint",
                "prettier",
            ],

            # Rules configuration
            "rules": {
                // Possible errors
                "no-console": "warn",
                "no-debugger": "error",
                "no-duplicate-imports": "error",

                /* Best practices */
                "curly": ["error", "all",],
                "eqeqeq": ["error", "always",],
                "no-eval": "error",
                "no-implied-eval": "error",

                // React specific
                "react/prop-types": "off",
                "react/react-in-jsx-scope": "off",
                "react-hooks/rules-of-hooks": "error",
                "react-hooks/exhaustive-deps": "warn",

                # TypeScript specific
                "@typescript-eslint/no-unused-vars": ["error", {
                    "argsIgnorePattern": "^_",
                    "varsIgnorePattern": "^_",
                },],
                "@typescript-eslint/explicit-function-return-type": "off",
                "@typescript-eslint/no-explicit-any": "warn",

                // Stylistic
                "indent": ["error", 2,],
                "linebreak-style": ["error", "unix",],
                "quotes": ["error", "single",],
                "semi": ["error", "always",],
            },

            "settings": {
                "react": {
                    "version": "detect",
                },
            },
        }"""

        result = loads_relaxed(json_str, repair_log=repair_log)

        # Verify structure
        assert result["parser"] == "@typescript-eslint/parser"
        assert "react" in result["plugins"]
        assert result["rules"]["no-console"] == "warn"

        # Verify repairs
        assert len(repair_log) >= 15
        kinds = {r.kind for r in repair_log}
        assert RepairKind.SINGLE_LINE_COMMENT in kinds
        assert RepairKind.MULTI_LINE_COMMENT in kinds
        assert RepairKind.HASH_COMMENT in kinds
        assert RepairKind.TRAILING_COMMA in kinds

    def test_package_json_with_errors(self, repair_log: list) -> None:
        """package.json with common mistakes."""
        json_str = """{
            'name': '@myorg/awesome-package',
            'version': '2.1.0',
            'description': 'An awesome package for doing awesome things',
            'main': 'dist/index.js',
            'module': 'dist/index.esm.js',
            'types': 'dist/index.d.ts',

            'scripts': {
                'build': 'rollup -c',
                'build:watch': 'rollup -c -w',
                'test': 'jest',
                'test:watch': 'jest --watch',
                'test:coverage': 'jest --coverage',
                'lint': 'eslint src --ext .ts,.tsx',
                'lint:fix': 'eslint src --ext .ts,.tsx --fix',
                'format': 'prettier --write src/**/*.ts',
                'prepublishOnly': 'npm run build',
                'typecheck': 'tsc --noEmit',
            },

            'keywords': [
                'typescript',
                'library',
                'utility',
                'tools',
            ],

            'author': {
                'name': 'John Doe',
                'email': 'john@example.com',
                'url': 'https://johndoe.com',
            },

            'license': 'MIT',

            'repository': {
                'type': 'git',
                'url': 'https://github.com/myorg/awesome-package.git',
            },

            'bugs': {
                'url': 'https://github.com/myorg/awesome-package/issues',
            },

            'homepage': 'https://github.com/myorg/awesome-package#readme',

            'dependencies': {
                'lodash': '^4.17.21',
                'axios': '^1.6.0',
                'dayjs': '^1.11.10',
            },

            'devDependencies': {
                'typescript': '^5.3.0',
                '@types/node': '^20.10.0',
                '@types/jest': '^29.5.0',
                'jest': '^29.7.0',
                'ts-jest': '^29.1.0',
                'rollup': '^4.6.0',
                '@rollup/plugin-typescript': '^11.1.0',
                'eslint': '^8.55.0',
                'prettier': '^3.1.0',
            },

            'peerDependencies': {
                'react': '>=17.0.0',
                'react-dom': '>=17.0.0',
            },

            'engines': {
                'node': '>=18.0.0',
                'npm': '>=9.0.0',
            },
        }"""

        result = loads_relaxed(json_str, repair_log=repair_log)

        # Verify structure
        assert result["name"] == "@myorg/awesome-package"
        assert result["version"] == "2.1.0"
        assert "lodash" in result["dependencies"]

        # Verify single quote repairs
        single_quote_repairs = [
            r for r in repair_log if r.kind == RepairKind.SINGLE_QUOTE_STRING
        ]
        assert len(single_quote_repairs) >= 20

        # Verify trailing commas
        trailing_repairs = [
            r for r in repair_log if r.kind == RepairKind.TRAILING_COMMA
        ]
        assert len(trailing_repairs) >= 10


class TestComplexLLMOutput:
    """Test complex LLM output with multiple issues."""

    def test_chatgpt_analysis_response(self, repair_log: list) -> None:
        """ChatGPT analysis with Python literals and trailing commas."""
        json_str = """{
            "analysis_id": "analysis_20240115_001",
            "model": "gpt-4-turbo",
            "timestamp": "2024-01-15T10:30:00Z",

            "input_summary": {
                "document_type": "financial_report",
                "pages": 45,
                "word_count": 12500,
                "language": "en",
            },

            "sentiment_analysis": {
                "overall_sentiment": "positive",
                "confidence": 0.87,
                "breakdown": {
                    "positive_phrases": 145,
                    "negative_phrases": 32,
                    "neutral_phrases": 89,
                },
                "key_positive_topics": [
                    "revenue growth",
                    "market expansion",
                    "cost optimization",
                    "customer satisfaction",
                ],
                "key_negative_topics": [
                    "supply chain issues",
                    "regulatory concerns",
                ],
            },

            "entity_extraction": {
                "organizations": [
                    {"name": "Acme Corp", "mentions": 23, "sentiment": "positive",},
                    {"name": "GlobalTech Inc", "mentions": 15, "sentiment": "neutral",},
                    {"name": "MarketLeaders LLC", "mentions": 8, "sentiment": "positive",},
                ],
                "people": [
                    {"name": "John Smith", "role": "CEO", "mentions": 12,},
                    {"name": "Jane Doe", "role": "CFO", "mentions": 8,},
                ],
                "locations": [
                    "New York",
                    "San Francisco",
                    "London",
                    "Tokyo",
                ],
                "dates": [
                    "Q4 2023",
                    "FY 2024",
                    "January 2024",
                ],
            },

            "financial_metrics": {
                "revenue": {"value": 15000000, "currency": "USD", "growth": 0.15,},
                "profit": {"value": 3500000, "currency": "USD", "growth": 0.22,},
                "expenses": {"value": 11500000, "currency": "USD", "growth": 0.08,},
            },

            "recommendations": [
                {
                    "priority": "high",
                    "category": "growth",
                    "description": "Expand into Asian markets",
                    "confidence": 0.82,
                    "actionable": True,
                },
                {
                    "priority": "medium",
                    "category": "efficiency",
                    "description": "Optimize supply chain operations",
                    "confidence": 0.75,
                    "actionable": True,
                },
                {
                    "priority": "low",
                    "category": "risk",
                    "description": "Monitor regulatory changes",
                    "confidence": 0.68,
                    "actionable": False,
                },
            ],

            "metadata": {
                "processing_time_ms": 4523,
                "tokens_used": 8945,
                "model_version": "gpt-4-turbo-2024-01-09",
                "is_complete": True,
                "has_errors": False,
                "truncated": None,
            },
        }"""

        result = loads_relaxed(json_str, repair_log=repair_log)

        # Verify structure
        assert result["analysis_id"] == "analysis_20240115_001"
        assert result["sentiment_analysis"]["confidence"] == 0.87
        assert len(result["recommendations"]) == 3
        assert result["metadata"]["is_complete"] is True

        # Verify Python literal repairs
        python_repairs = [
            r for r in repair_log if r.kind == RepairKind.PYTHON_LITERAL
        ]
        assert len(python_repairs) >= 5  # True, False, None

        # Verify trailing comma repairs
        trailing_repairs = [
            r for r in repair_log if r.kind == RepairKind.TRAILING_COMMA
        ]
        assert len(trailing_repairs) >= 15

    def test_claude_structured_output(self, repair_log: list) -> None:
        """Claude structured output with nested data."""
        json_str = """{
            response_type: 'structured_analysis',
            request_id: 'req_abc123xyz',

            content: {
                title: 'Code Review Analysis',
                summary: 'The submitted code has several areas for improvement',

                findings: [
                    {
                        severity: 'high',
                        category: 'security',
                        line_numbers: [45, 67, 123,],
                        description: 'SQL injection vulnerability detected',
                        recommendation: 'Use parameterized queries',
                        affected_files: ['src/db/queries.py', 'src/api/handlers.py',],
                    },
                    {
                        severity: 'medium',
                        category: 'performance',
                        line_numbers: [89, 90, 91,],
                        description: 'N+1 query pattern detected',
                        recommendation: 'Use batch fetching or eager loading',
                        affected_files: ['src/services/user_service.py',],
                    },
                    {
                        severity: 'low',
                        category: 'style',
                        line_numbers: [12, 34, 56, 78,],
                        description: 'Inconsistent naming conventions',
                        recommendation: 'Follow PEP 8 naming guidelines',
                        affected_files: ['src/utils/helpers.py', 'src/models/user.py',],
                    },
                ],

                metrics: {
                    total_lines: 2456,
                    lines_analyzed: 2456,
                    issues_found: 12,
                    critical_issues: 1,
                    suggestions: 8,
                    coverage_percent: 100.0,
                },

                file_analysis: {
                    'src/db/queries.py': {
                        lines: 234,
                        issues: 3,
                        complexity_score: 7.8,
                    },
                    'src/api/handlers.py': {
                        lines: 456,
                        issues: 2,
                        complexity_score: 6.2,
                    },
                    'src/services/user_service.py': {
                        lines: 189,
                        issues: 4,
                        complexity_score: 5.5,
                    },
                },
            },

            usage: {
                input_tokens: 15234,
                output_tokens: 2341,
                total_tokens: 17575,
            },
        }"""

        result = loads_relaxed(json_str, repair_log=repair_log)

        # Verify structure
        assert result["response_type"] == "structured_analysis"
        assert len(result["content"]["findings"]) == 3
        assert result["content"]["metrics"]["total_lines"] == 2456

        # Verify unquoted key repairs
        unquoted_repairs = [
            r for r in repair_log if r.kind == RepairKind.UNQUOTED_KEY
        ]
        assert len(unquoted_repairs) >= 10

        # Verify single quote repairs
        single_quote_repairs = [
            r for r in repair_log if r.kind == RepairKind.SINGLE_QUOTE_STRING
        ]
        assert len(single_quote_repairs) >= 15

    def test_llm_function_call_complex(self, repair_log: list) -> None:
        """Complex function call with multiple arguments."""
        # Note: Due to normalizer processing order (unquoted keys run before comment
        # stripping), unquoted keys must not appear directly after comments. We use
        # quoted keys after comments and unquoted keys only in positions without
        # preceding comments on the same line/structure.
        json_str = """{
            // Function call request from LLM
            "function_name": "create_project",

            /* Arguments for the function */
            "arguments": {
                "name": "MyAwesomeProject",
                "description": "A project that does awesome things",

                // Project configuration
                "config": {
                    language: "python",
                    framework: "fastapi",
                    database: "postgresql",
                    cache: "redis",
                    use_docker: True,
                    use_kubernetes: False,
                    ci_cd: "github_actions",
                },

                // Team settings
                "team": {
                    owner: "john.doe@example.com",
                    admins: [
                        "jane.smith@example.com",
                        "bob.wilson@example.com",
                    ],
                    members: [
                        "alice.johnson@example.com",
                        "charlie.brown@example.com",
                        "diana.prince@example.com",
                    ],
                    notifications_enabled: True,
                },

                /* Repository settings */
                "repository": {
                    visibility: "private",
                    default_branch: "main",
                    enable_issues: True,
                    enable_wiki: False,
                    enable_discussions: True,
                    auto_init: True,
                    gitignore_template: "Python",
                    license_template: "mit",
                },

                // Initial structure
                "initial_files": [
                    "README.md",
                    "requirements.txt",
                    "pyproject.toml",
                    "Dockerfile",
                    ".github/workflows/ci.yml",
                ],
            },

            # Metadata section
            "metadata": {
                "request_id": "func_call_001",
                "timestamp": "2024-01-15T14:30:00Z",
                "model": "gpt-4-turbo",
                "temperature": 0.7,
                "max_tokens": None,
            },
        }"""

        result = loads_relaxed(json_str, repair_log=repair_log)

        # Verify structure
        assert result["function_name"] == "create_project"
        assert result["arguments"]["config"]["language"] == "python"
        assert result["arguments"]["team"]["notifications_enabled"] is True

        # Verify multiple repair kinds
        kinds = {r.kind for r in repair_log}
        assert RepairKind.SINGLE_LINE_COMMENT in kinds
        assert RepairKind.MULTI_LINE_COMMENT in kinds
        assert RepairKind.HASH_COMMENT in kinds
        assert RepairKind.UNQUOTED_KEY in kinds
        assert RepairKind.PYTHON_LITERAL in kinds
        assert RepairKind.TRAILING_COMMA in kinds


class TestComplexAPIResponses:
    """Test large API responses with embedded errors."""

    def test_user_list_response(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """List of 20+ users with various issues."""
        left = smart_double_quotes["left"]
        right = smart_double_quotes["right"]

        json_str = f"""{{
            "status": "success",
            "total_count": 25,
            "page": 1,
            "per_page": 25,

            "users": [
                {{"id": 1, "name": "Alice Johnson", "email": "alice@example.com", "role": "admin", "active": True,}},
                {{"id": 2, "name": "Bob Smith", "email": "bob@example.com", "role": "user", "active": True,}},
                {{"id": 3, "name": "Charlie Brown", "email": "charlie@example.com", "role": "user", "active": False,}},
                {{"id": 4, "name": "Diana Prince", "email": "diana@example.com", "role": "moderator", "active": True,}},
                {{"id": 5, "name": "Edward Norton", "email": "edward@example.com", "role": "user", "active": True,}},
                {{"id": 6, "name": {left}Fiona Green{right}, "email": "fiona@example.com", "role": "user", "active": True,}},
                {{"id": 7, "name": "George Wilson", "email": "george@example.com", "role": "admin", "active": True,}},
                {{"id": 8, "name": "Hannah Montana", "email": "hannah@example.com", "role": "user", "active": False,}},
                {{"id": 9, "name": {left}Ivan Petrov{right}, "email": "ivan@example.com", "role": "user", "active": True,}},
                {{"id": 10, "name": "Julia Roberts", "email": "julia@example.com", "role": "moderator", "active": True,}},
                {{"id": 11, "name": "Kevin Hart", "email": "kevin@example.com", "role": "user", "active": True,}},
                {{"id": 12, "name": "Laura Palmer", "email": "laura@example.com", "role": "user", "active": False,}},
                {{"id": 13, "name": {left}Michael Scott{right}, "email": "michael@example.com", "role": "user", "active": True,}},
                {{"id": 14, "name": "Nancy Drew", "email": "nancy@example.com", "role": "admin", "active": True,}},
                {{"id": 15, "name": "Oscar Wilde", "email": "oscar@example.com", "role": "user", "active": True,}},
                {{"id": 16, "name": "Patricia Arquette", "email": "patricia@example.com", "role": "user", "active": True,}},
                {{"id": 17, "name": "Quentin Tarantino", "email": "quentin@example.com", "role": "user", "active": False,}},
                {{"id": 18, "name": {left}Rachel Green{right}, "email": "rachel@example.com", "role": "moderator", "active": True,}},
                {{"id": 19, "name": "Steve Rogers", "email": "steve@example.com", "role": "user", "active": True,}},
                {{"id": 20, "name": "Tina Turner", "email": "tina@example.com", "role": "user", "active": True,}},
            ],

            "metadata": {{
                "generated_at": "2024-01-15T12:00:00Z",
                "cache_hit": False,
                "query_time_ms": 45,
            }},
        }}"""

        result = loads_relaxed(json_str, repair_log=repair_log)

        # Verify structure
        assert result["total_count"] == 25
        assert len(result["users"]) == 20
        assert result["users"][0]["name"] == "Alice Johnson"
        assert result["metadata"]["cache_hit"] is False

        # Verify smart quote repairs
        smart_quote_repairs = [
            r for r in repair_log if r.kind == RepairKind.SMART_QUOTE
        ]
        assert len(smart_quote_repairs) >= 8  # 4 names with smart quotes (left+right)

        # Verify Python literal repairs
        python_repairs = [
            r for r in repair_log if r.kind == RepairKind.PYTHON_LITERAL
        ]
        assert len(python_repairs) >= 20  # True/False for each user

    def test_analytics_dashboard_data(self, repair_log: list) -> None:
        """Analytics data with comments and annotations."""
        json_str = """{
            // Dashboard: Sales Analytics
            // Generated: 2024-01-15
            // Period: Q4 2023

            "dashboard_id": "sales_q4_2023",
            "title": "Q4 2023 Sales Performance",

            /* Summary metrics */
            "summary": {
                "total_revenue": 15750000.00,
                "total_orders": 45230,
                "average_order_value": 348.25,
                "conversion_rate": 0.0342,
                "year_over_year_growth": 0.156,
            },

            // Monthly breakdown
            "monthly_data": [
                {
                    "month": "October",
                    "revenue": 4850000.00,
                    "orders": 13920,
                    "avg_order": 348.42,
                    # First month of quarter
                    "notes": "Product launch impact",
                },
                {
                    "month": "November",
                    "revenue": 5200000.00,
                    "orders": 14850,
                    "avg_order": 350.17,
                    # Black Friday included
                    "notes": "Black Friday peak",
                },
                {
                    "month": "December",
                    "revenue": 5700000.00,
                    "orders": 16460,
                    "avg_order": 346.29,
                    # Holiday season
                    "notes": "Holiday season performance",
                },
            ],

            /* Regional performance */
            "regions": {
                "north_america": {
                    "revenue": 8500000.00,
                    "percentage": 0.54,
                    "growth": 0.18,
                    "top_products": ["Widget Pro", "Gadget Plus", "Tool Master",],
                },
                "europe": {
                    "revenue": 4200000.00,
                    "percentage": 0.27,
                    "growth": 0.12,
                    "top_products": ["Widget Pro", "Service Pack", "Tool Basic",],
                },
                "asia_pacific": {
                    "revenue": 3050000.00,
                    "percentage": 0.19,
                    "growth": 0.22,
                    "top_products": ["Gadget Plus", "Widget Lite", "Tool Master",],
                },
            },

            // Product category breakdown
            "categories": [
                {"name": "Widgets", "revenue": 6500000.00, "units": 18500, "margin": 0.42,},
                {"name": "Gadgets", "revenue": 5250000.00, "units": 12300, "margin": 0.38,},
                {"name": "Tools", "revenue": 2500000.00, "units": 8900, "margin": 0.45,},
                {"name": "Services", "revenue": 1500000.00, "units": 5530, "margin": 0.65,},
            ],

            /* Customer segments */
            "customer_segments": {
                "enterprise": {
                    "customers": 245,
                    "revenue": 9800000.00,
                    "avg_deal_size": 40000.00,
                    "retention_rate": 0.94,
                },
                "mid_market": {
                    "customers": 1230,
                    "revenue": 4200000.00,
                    "avg_deal_size": 3414.63,
                    "retention_rate": 0.87,
                },
                "small_business": {
                    "customers": 8750,
                    "revenue": 1750000.00,
                    "avg_deal_size": 200.00,
                    "retention_rate": 0.72,
                },
            },

            # Report metadata
            "metadata": {
                "generated_by": "analytics_service_v2",
                "generation_time_ms": 1234,
                "data_freshness": "2024-01-15T00:00:00Z",
                "includes_estimates": False,
            },
        }"""

        result = loads_relaxed(json_str, repair_log=repair_log)

        # Verify structure
        assert result["dashboard_id"] == "sales_q4_2023"
        assert result["summary"]["total_revenue"] == 15750000.00
        assert len(result["monthly_data"]) == 3
        assert len(result["categories"]) == 4

        # Verify we have all comment types
        kinds = {r.kind for r in repair_log}
        assert RepairKind.SINGLE_LINE_COMMENT in kinds
        assert RepairKind.MULTI_LINE_COMMENT in kinds
        assert RepairKind.HASH_COMMENT in kinds
        assert RepairKind.TRAILING_COMMA in kinds

        # Should have many repairs
        assert len(repair_log) >= 25

    def test_nested_api_response(self, repair_log: list) -> None:
        """Deeply nested response (5+ levels)."""
        json_str = """{
            "api_version": "v2",
            "request_id": "req_nested_001",

            "data": {
                "organization": {
                    "id": "org_123",
                    "name": "TechCorp Industries",

                    "departments": {
                        "engineering": {
                            "head": "Jane Smith",
                            "budget": 5000000,

                            "teams": {
                                "frontend": {
                                    "lead": "Alice Brown",
                                    "members": 12,

                                    "projects": {
                                        "dashboard_v2": {
                                            "status": "active",
                                            "progress": 0.75,
                                            "tasks_completed": 45,
                                            "tasks_remaining": 15,

                                            "milestones": [
                                                {"name": "Design", "completed": True,},
                                                {"name": "Development", "completed": True,},
                                                {"name": "Testing", "completed": False,},
                                                {"name": "Deployment", "completed": False,},
                                            ],
                                        },
                                        "mobile_app": {
                                            "status": "planning",
                                            "progress": 0.15,
                                            "tasks_completed": 8,
                                            "tasks_remaining": 45,

                                            "milestones": [
                                                {"name": "Requirements", "completed": True,},
                                                {"name": "Design", "completed": False,},
                                                {"name": "Development", "completed": False,},
                                                {"name": "Testing", "completed": False,},
                                            ],
                                        },
                                    },
                                },
                                "backend": {
                                    "lead": "Bob Wilson",
                                    "members": 15,

                                    "projects": {
                                        "api_v3": {
                                            "status": "active",
                                            "progress": 0.60,
                                            "tasks_completed": 30,
                                            "tasks_remaining": 20,

                                            "milestones": [
                                                {"name": "Architecture", "completed": True,},
                                                {"name": "Core Services", "completed": True,},
                                                {"name": "Integration", "completed": False,},
                                                {"name": "Documentation", "completed": False,},
                                            ],
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },

            "pagination": {
                "has_more": False,
                "next_cursor": None,
            },
        }"""

        result = loads_relaxed(json_str, repair_log=repair_log)

        # Verify deeply nested structure
        frontend = result["data"]["organization"]["departments"]["engineering"]["teams"]["frontend"]
        assert frontend["lead"] == "Alice Brown"
        assert frontend["projects"]["dashboard_v2"]["progress"] == 0.75

        # Verify Python literal repairs
        python_repairs = [
            r for r in repair_log if r.kind == RepairKind.PYTHON_LITERAL
        ]
        assert len(python_repairs) >= 10

        # Verify trailing comma repairs
        trailing_repairs = [
            r for r in repair_log if r.kind == RepairKind.TRAILING_COMMA
        ]
        assert len(trailing_repairs) >= 20


class TestManyErrorsEdgeCases:
    """Stress tests with many errors."""

    def test_50_trailing_commas(self, repair_log: list) -> None:
        """JSON with 50 trailing commas."""
        # Generate 50 objects with trailing commas
        items = [f'{{"id": {i}, "value": "item_{i}",}}' for i in range(50)]
        json_str = "[" + ",".join(items) + ",]"

        result = loads_relaxed(json_str, repair_log=repair_log)

        # Verify structure
        assert len(result) == 50
        assert result[0]["id"] == 0
        assert result[49]["id"] == 49

        # Verify all 51 trailing commas were tracked (50 in objects + 1 in array)
        trailing_repairs = [
            r for r in repair_log if r.kind == RepairKind.TRAILING_COMMA
        ]
        assert len(trailing_repairs) == 51

    def test_all_11_repair_kinds(
        self, repair_log: list, smart_double_quotes: dict[str, str]
    ) -> None:
        """Single JSON containing all 11 RepairKind types."""
        left = smart_double_quotes["left"]
        right = smart_double_quotes["right"]

        # Construct JSON with all 11 error types
        json_str = f'''{{
            // Single-line comment (SINGLE_LINE_COMMENT)
            /* Multi-line comment (MULTI_LINE_COMMENT) */
            # Hash comment (HASH_COMMENT)
            {left}smart_key{right}: {left}smart_value{right},
            'single_key': 'single_value',
            unquoted_key: "quoted_value",
            "python_bool": True,
            "python_none": None,
            "text_with_newline": "line1
line2",
            "truncated_array": [1, 2, 3, ...],
            "trailing_comma": "present",
        '''  # Missing closing bracket

        result = loads_relaxed(json_str, repair_log=repair_log)

        # Verify structure was parsed
        assert result["smart_key"] == "smart_value"
        assert result["single_key"] == "single_value"
        assert result["unquoted_key"] == "quoted_value"
        assert result["python_bool"] is True
        assert result["python_none"] is None
        assert "line1" in result["text_with_newline"]
        assert result["truncated_array"] == [1, 2, 3]

        # Verify all 11 repair kinds are present
        kinds = {r.kind for r in repair_log}

        assert RepairKind.SINGLE_LINE_COMMENT in kinds, "Missing SINGLE_LINE_COMMENT"
        assert RepairKind.MULTI_LINE_COMMENT in kinds, "Missing MULTI_LINE_COMMENT"
        assert RepairKind.HASH_COMMENT in kinds, "Missing HASH_COMMENT"
        assert RepairKind.SMART_QUOTE in kinds, "Missing SMART_QUOTE"
        assert RepairKind.SINGLE_QUOTE_STRING in kinds, "Missing SINGLE_QUOTE_STRING"
        assert RepairKind.UNQUOTED_KEY in kinds, "Missing UNQUOTED_KEY"
        assert RepairKind.PYTHON_LITERAL in kinds, "Missing PYTHON_LITERAL"
        assert RepairKind.UNESCAPED_NEWLINE in kinds, "Missing UNESCAPED_NEWLINE"
        assert RepairKind.TRUNCATION_MARKER in kinds, "Missing TRUNCATION_MARKER"
        assert RepairKind.TRAILING_COMMA in kinds, "Missing TRAILING_COMMA"
        assert RepairKind.MISSING_BRACKET in kinds, "Missing MISSING_BRACKET"

        assert len(kinds) == 11, f"Expected 11 repair kinds, got {len(kinds)}: {kinds}"

    def test_mixed_errors_every_line(self, repair_log: list) -> None:
        """JSON with many different error types across multiple lines."""
        # Note: Comments are stripped after other normalizers run, so keys/values
        # immediately after comments must use double quotes or single quotes (not unquoted).
        # Unquoted keys work when there's no comment between the preceding {/, and the key.
        json_str = """{
            // Comment section 1
            "key1": "value1",
            "key2": "value2",
            // Comment section 2
            "key3": "value3",
            'key4': 'value4',
            'key5': 'value5',
            'key6': 'value6',
            /* Multi-line comment */
            "key7": "value7",
            "bool1": True,
            "bool2": False,
            "null1": None,
            'key10': 'value10',
            'key11': 'value11',
            'key12': 'value12',
            # Hash comment before key
            "key13": "value13",
            'key14': 'value14',
            'key15': 'value15',
            "nested": {
                unquoted1: "unquoted key here",
                unquoted2: "another unquoted key",
                unquoted3: "third unquoted key",
            },
        }"""

        result = loads_relaxed(json_str, repair_log=repair_log)

        # Verify structure
        assert result["key4"] == "value4"
        assert result["nested"]["unquoted1"] == "unquoted key here"
        assert result["bool1"] is True
        assert result["null1"] is None

        # Should have many repairs (comments + single quotes + unquoted + python literals + trailing)
        assert len(repair_log) >= 20

        # Verify variety of repair kinds
        kinds = {r.kind for r in repair_log}
        assert len(kinds) >= 5  # At least 5 different repair kinds

    def test_100_single_quote_strings(self, repair_log: list) -> None:
        """JSON with 100 single-quoted strings."""
        items = [f"'item_{i}'" for i in range(100)]
        json_str = "[" + ", ".join(items) + "]"

        result = loads_relaxed(json_str, repair_log=repair_log)

        # Verify structure
        assert len(result) == 100
        assert result[0] == "item_0"
        assert result[99] == "item_99"

        # Verify all 100 single-quote repairs
        single_quote_repairs = [
            r for r in repair_log if r.kind == RepairKind.SINGLE_QUOTE_STRING
        ]
        assert len(single_quote_repairs) == 100
