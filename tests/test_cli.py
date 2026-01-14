"""Tests for jsonfix CLI."""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from jsonfix.cli import main, parse_args, process_file

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture


class TestParseArgs:
    """Tests for argument parsing."""

    def test_single_file(self) -> None:
        args = parse_args(["test.json"])
        assert args.files == ["test.json"]
        assert args.output is None
        assert args.verbose is False
        assert args.backup is False
        assert args.dry_run is False

    def test_multiple_files(self) -> None:
        args = parse_args(["a.json", "b.json", "c.json"])
        assert args.files == ["a.json", "b.json", "c.json"]

    def test_output_option(self) -> None:
        args = parse_args(["input.json", "-o", "output.json"])
        assert args.files == ["input.json"]
        assert args.output == "output.json"

    def test_output_option_long(self) -> None:
        args = parse_args(["input.json", "--output", "output.json"])
        assert args.output == "output.json"

    def test_verbose_flag(self) -> None:
        args = parse_args(["-v", "test.json"])
        assert args.verbose is True

    def test_verbose_flag_long(self) -> None:
        args = parse_args(["--verbose", "test.json"])
        assert args.verbose is True

    def test_backup_flag(self) -> None:
        args = parse_args(["-b", "test.json"])
        assert args.backup is True

    def test_backup_flag_long(self) -> None:
        args = parse_args(["--backup", "test.json"])
        assert args.backup is True

    def test_dry_run_flag(self) -> None:
        args = parse_args(["--dry-run", "test.json"])
        assert args.dry_run is True

    def test_stdin(self) -> None:
        args = parse_args(["-"])
        assert args.files == ["-"]

    def test_combined_flags(self) -> None:
        args = parse_args(["-v", "-b", "--dry-run", "test.json"])
        assert args.verbose is True
        assert args.backup is True
        assert args.dry_run is True


class TestProcessFile:
    """Tests for file processing."""

    def test_fix_trailing_comma(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.json"
        test_file.write_text('{"a": 1,}')

        stdout = io.StringIO()
        stderr = io.StringIO()

        result = process_file(
            str(test_file),
            output_path=None,
            verbose=False,
            backup=False,
            dry_run=False,
            out_stream=stdout,
            err_stream=stderr,
        )

        assert result is True
        content = test_file.read_text()
        assert content == '{\n  "a": 1\n}\n'

    def test_fix_comments(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.json"
        test_file.write_text('{\n  // comment\n  "a": 1\n}')

        result = process_file(
            str(test_file),
            output_path=None,
            verbose=False,
            backup=False,
            dry_run=False,
        )

        assert result is True
        content = test_file.read_text()
        assert "comment" not in content
        assert '"a": 1' in content

    def test_verbose_output(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.json"
        test_file.write_text('{"a": 1,}')

        stderr = io.StringIO()
        result = process_file(
            str(test_file),
            output_path=None,
            verbose=True,
            backup=False,
            dry_run=False,
            err_stream=stderr,
        )

        assert result is True
        output = stderr.getvalue()
        assert "Fixed 1 issue" in output
        assert "trailing comma" in output.lower()

    def test_verbose_no_changes(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.json"
        test_file.write_text('{"a": 1}')

        stderr = io.StringIO()
        result = process_file(
            str(test_file),
            output_path=None,
            verbose=True,
            backup=False,
            dry_run=False,
            err_stream=stderr,
        )

        assert result is True
        assert "No changes needed" in stderr.getvalue()

    def test_output_to_different_file(self, tmp_path: Path) -> None:
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"
        input_file.write_text('{"a": 1,}')

        result = process_file(
            str(input_file),
            output_path=str(output_file),
            verbose=False,
            backup=False,
            dry_run=False,
        )

        assert result is True
        # Input unchanged (still has trailing comma in original)
        assert input_file.read_text() == '{"a": 1,}'
        # Output has fixed JSON
        assert output_file.read_text() == '{\n  "a": 1\n}\n'

    def test_backup_creation(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.json"
        test_file.write_text('{"a": 1,}')

        result = process_file(
            str(test_file),
            output_path=None,
            verbose=False,
            backup=True,
            dry_run=False,
        )

        assert result is True
        backup_file = tmp_path / "test.json.bak"
        assert backup_file.exists()
        assert backup_file.read_text() == '{"a": 1,}'

    def test_dry_run(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.json"
        original = '{"a": 1,}'
        test_file.write_text(original)

        stderr = io.StringIO()
        result = process_file(
            str(test_file),
            output_path=None,
            verbose=False,
            backup=False,
            dry_run=True,
            err_stream=stderr,
        )

        assert result is True
        # File should be unchanged
        assert test_file.read_text() == original
        assert "Would fix 1 issue" in stderr.getvalue()

    def test_file_not_found(self) -> None:
        stderr = io.StringIO()
        result = process_file(
            "/nonexistent/file.json",
            output_path=None,
            verbose=False,
            backup=False,
            dry_run=False,
            err_stream=stderr,
        )

        assert result is False
        assert "File not found" in stderr.getvalue()

    def test_invalid_json(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.json"
        test_file.write_text("not valid json at all {{{")

        stderr = io.StringIO()
        result = process_file(
            str(test_file),
            output_path=None,
            verbose=False,
            backup=False,
            dry_run=False,
            err_stream=stderr,
        )

        assert result is False
        assert "Error parsing" in stderr.getvalue()

    def test_stdout_output(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.json"
        test_file.write_text('{"a": 1,}')

        stdout = io.StringIO()
        result = process_file(
            str(test_file),
            output_path="-",
            verbose=False,
            backup=False,
            dry_run=False,
            out_stream=stdout,
        )

        assert result is True
        # Should write to stdout without trailing newline for pipe compatibility
        output = stdout.getvalue()
        assert '"a": 1' in output


class TestMain:
    """Tests for main CLI entry point."""

    def test_single_file_success(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.json"
        test_file.write_text('{"a": 1,}')

        exit_code = main([str(test_file)])

        assert exit_code == 0
        assert '{\n  "a": 1\n}\n' == test_file.read_text()

    def test_multiple_files(self, tmp_path: Path) -> None:
        file1 = tmp_path / "a.json"
        file2 = tmp_path / "b.json"
        file1.write_text('{"a": 1,}')
        file2.write_text('{"b": 2,}')

        exit_code = main([str(file1), str(file2)])

        assert exit_code == 0
        assert '"a": 1' in file1.read_text()
        assert '"b": 2' in file2.read_text()

    def test_output_with_multiple_files_error(
        self, tmp_path: Path, capsys: CaptureFixture[str]
    ) -> None:
        file1 = tmp_path / "a.json"
        file2 = tmp_path / "b.json"
        file1.write_text('{"a": 1}')
        file2.write_text('{"b": 2}')

        exit_code = main([str(file1), str(file2), "-o", "out.json"])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "--output can only be used with a single input file" in captured.err

    def test_partial_failure(self, tmp_path: Path) -> None:
        good_file = tmp_path / "good.json"
        good_file.write_text('{"a": 1,}')

        exit_code = main([str(good_file), "/nonexistent/bad.json"])

        assert exit_code == 1
        # Good file should still be fixed
        assert '"a": 1' in good_file.read_text()


class TestStdinStdout:
    """Tests for stdin/stdout handling."""

    def test_stdin_stdout_subprocess(self, tmp_path: Path) -> None:
        """Test stdin/stdout via subprocess for realistic behavior."""
        input_json = '{"a": 1,}'

        result = subprocess.run(
            [sys.executable, "-m", "jsonfix.cli", "-"],
            input=input_json,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert '"a": 1' in result.stdout

    def test_file_to_stdout_subprocess(self, tmp_path: Path) -> None:
        """Test reading file and writing to stdout."""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"a": 1,}')

        result = subprocess.run(
            [sys.executable, "-m", "jsonfix.cli", str(test_file), "-o", "-"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert '"a": 1' in result.stdout
        # Original file should be unchanged
        assert test_file.read_text() == '{"a": 1,}'


class TestVersion:
    """Tests for version flag."""

    def test_version_flag(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "jsonfix.cli", "--version"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "jsonfix" in result.stdout
        assert "0.1.0" in result.stdout
