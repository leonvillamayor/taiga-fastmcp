#!/usr/bin/env python3
"""Add type annotations to test functions.

This script adds `-> None` return type annotations to test functions
that are missing them, as required by mypy strict mode.
"""

import re
import sys
from pathlib import Path


def fix_function_annotations(content: str) -> str:
    """Add `-> None` to functions that don't have return type annotations.

    Args:
        content: The file content to process

    Returns:
        The modified content with type annotations added
    """
    # Pattern to match function definitions without return type
    # Matches: async def funcname(args):  or  def funcname(args):
    # Where there's no -> before the colon
    patterns = [
        # Match async def test_* functions without return type
        (
            r"(\s*)(async def test_[a-zA-Z0-9_]+\([^)]*\))(\s*):",
            r"\1\2 -> None:",
        ),
        # Match def test_* functions without return type
        (
            r"(\s*)(def test_[a-zA-Z0-9_]+\([^)]*\))(\s*):",
            r"\1\2 -> None:",
        ),
        # Match async def fixture functions (like setup_method, etc)
        (
            r"(\s*)(async def [a-zA-Z0-9_]+\([^)]*\))(\s*):",
            r"\1\2 -> None:",
        ),
        # Match def fixture functions
        (
            r"(\s*)(def [a-zA-Z0-9_]+\([^)]*\))(\s*):",
            r"\1\2 -> None:",
        ),
    ]

    result = content
    for pattern, replacement in patterns:
        # Only replace if there's no `->` already present before the colon
        lines = result.split("\n")
        new_lines = []
        for line in lines:
            # Check if line matches pattern and doesn't already have ->
            if re.match(pattern, line) and "->" not in line:
                new_line = re.sub(pattern, replacement, line)
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        result = "\n".join(new_lines)

    return result


def process_file(filepath: Path) -> bool:
    """Process a single file and add type annotations.

    Args:
        filepath: Path to the file to process

    Returns:
        True if file was modified, False otherwise
    """
    content = filepath.read_text()
    new_content = fix_function_annotations(content)

    if content != new_content:
        filepath.write_text(new_content)
        return True
    return False


def main() -> int:
    """Main entry point."""
    tests_dir = Path("tests")

    if not tests_dir.exists():
        print("Error: tests/ directory not found")
        return 1

    modified_count = 0
    total_count = 0

    for filepath in tests_dir.rglob("*.py"):
        total_count += 1
        if process_file(filepath):
            modified_count += 1
            print(f"Modified: {filepath}")

    print(f"\nProcessed {total_count} files, modified {modified_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
