"""Command-line interface for jsonfix."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import TextIO

from . import __version__, get_repairs, loads_relaxed


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="jsonfix",
        description="Fix 'almost JSON' files with trailing commas, comments, smart quotes, and more.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="JSON file(s) to fix. Use '-' for stdin.",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="Output file (default: overwrite input). Use '-' for stdout.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show repairs made.",
    )
    parser.add_argument(
        "-b",
        "--backup",
        action="store_true",
        help="Create .bak backup before overwriting.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args(args)


def read_input(path: str) -> tuple[str, str]:
    """Read input from file or stdin.

    Returns:
        Tuple of (content, display_name).
    """
    if path == "-":
        return sys.stdin.read(), "<stdin>"
    file_path = Path(path)
    return file_path.read_text(encoding="utf-8"), str(file_path)


def write_output(
    content: str,
    input_path: str,
    output_path: str | None,
    backup: bool,
    dry_run: bool,
    out_stream: TextIO = sys.stdout,
) -> None:
    """Write output to file or stdout."""
    if dry_run:
        return

    # Determine actual output destination
    if output_path == "-" or (input_path == "-" and output_path is None):
        out_stream.write(content)
        return

    dest = Path(output_path) if output_path else Path(input_path)

    # Create backup if requested and overwriting existing file
    if backup and dest.exists() and (output_path is None or output_path == input_path):
        backup_path = dest.with_suffix(dest.suffix + ".bak")
        shutil.copy2(dest, backup_path)

    dest.write_text(content, encoding="utf-8")


def process_file(
    path: str,
    output_path: str | None,
    verbose: bool,
    backup: bool,
    dry_run: bool,
    out_stream: TextIO = sys.stdout,
    err_stream: TextIO = sys.stderr,
) -> bool:
    """Process a single file.

    Returns:
        True if successful, False if error occurred.
    """
    try:
        content, display_name = read_input(path)
    except FileNotFoundError:
        err_stream.write(f"Error: File not found: {path}\n")
        return False
    except PermissionError:
        err_stream.write(f"Error: Permission denied: {path}\n")
        return False
    except OSError as e:
        err_stream.write(f"Error reading {path}: {e}\n")
        return False

    # Get repairs to show what was fixed
    repairs = get_repairs(content)

    # Parse and re-serialize to get fixed JSON
    try:
        import json
        data = loads_relaxed(content)
        fixed = json.dumps(data, indent=2, ensure_ascii=False)
        # Add trailing newline for files
        if output_path != "-" and not (path == "-" and output_path is None):
            fixed += "\n"
    except Exception as e:
        err_stream.write(f"Error parsing {display_name}: {e}\n")
        return False

    # Show repairs in verbose mode
    if verbose:
        if repairs:
            err_stream.write(f"Fixed {len(repairs)} issue(s) in {display_name}:\n")
            for repair in repairs:
                err_stream.write(f"  Line {repair.line}: {repair.message}\n")
        else:
            err_stream.write(f"No changes needed in {display_name}\n")

    # Show dry-run diff
    if dry_run:
        if repairs:
            err_stream.write(f"Would fix {len(repairs)} issue(s) in {display_name}\n")
        return True

    # Write output
    try:
        write_output(fixed, path, output_path, backup, dry_run, out_stream)
    except PermissionError:
        dest = output_path or path
        err_stream.write(f"Error: Permission denied writing to: {dest}\n")
        return False
    except OSError as e:
        dest = output_path or path
        err_stream.write(f"Error writing to {dest}: {e}\n")
        return False

    return True


def main(args: list[str] | None = None) -> int:
    """CLI entry point.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parsed = parse_args(args)

    # Validate: can only use -o with single file
    if parsed.output and len(parsed.files) > 1:
        sys.stderr.write("Error: --output can only be used with a single input file\n")
        return 1

    success = True
    for file_path in parsed.files:
        if not process_file(
            file_path,
            parsed.output,
            parsed.verbose,
            parsed.backup,
            parsed.dry_run,
        ):
            success = False

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
