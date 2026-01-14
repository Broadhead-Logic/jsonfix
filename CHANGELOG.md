# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Command-line interface (`jsonfix` command)
  - Fix JSON files in-place or to output file
  - Verbose mode (`-v`) to show repairs made
  - Backup mode (`-b`) to create `.bak` files
  - Dry-run mode (`--dry-run`) to preview changes
  - Stdin/stdout support for piping

## [0.1.0] - 2026-01-13

### Added
- Initial release
- Core relaxed JSON parsing (comments, trailing commas, smart quotes)
- V2 extensions (unquoted keys, single quotes, Python literals, auto-close brackets)
- LLM error handling (JSON extraction, markdown fences, unescaped quotes)
- Structural repairs (missing colons/commas, control characters, backslash escaping)
- Edge case handling (JavaScript values, hex/octal/binary numbers, double commas)
- Comprehensive repair logging with RepairKind enum
- 589 tests with 94%+ coverage
