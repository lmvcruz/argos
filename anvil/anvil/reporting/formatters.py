"""
Formatting utilities for reports.

This module provides formatting functions for durations, file paths,
issue locations, and other report elements.
"""

from pathlib import Path

from anvil.models.validator import Issue


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "1.50s" or "123ms")
    """
    if seconds < 0.1:
        return f"{int(seconds * 1000)}ms"
    else:
        return f"{seconds:.2f}s"


def format_file_path(file_path: str, base_path: Path = None) -> str:
    """
    Format file path as relative to base path.

    Args:
        file_path: Absolute or relative file path
        base_path: Base path to make relative to (defaults to current directory)

    Returns:
        Relative file path string with forward slashes
    """
    if base_path is None:
        base_path = Path.cwd()

    try:
        path = Path(file_path)
        if path.is_absolute():
            result = str(path.relative_to(base_path))
        else:
            result = str(path)
        # Use forward slashes for consistency
        return result.replace("\\", "/")
    except (ValueError, OSError):
        # If path is not relative to base_path, return as-is
        return file_path.replace("\\", "/")


def format_issue_location(issue: Issue) -> str:
    """
    Format issue location as "line:column" or "line" if no column.

    Args:
        issue: Issue to format location for

    Returns:
        Formatted location string
    """
    if issue.column_number is not None:
        return f"{issue.line_number}:{issue.column_number}"
    else:
        return str(issue.line_number)
