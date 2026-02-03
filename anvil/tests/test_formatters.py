"""
Tests for formatting utilities.

This module tests the formatting functions for durations, file paths,
issue locations, and other report elements.
"""

from pathlib import Path

from anvil.models.validator import Issue
from anvil.reporting.formatters import (
    format_duration,
    format_file_path,
    format_issue_location,
)


class TestFormatDuration:
    """Test format_duration function."""

    def test_format_duration_seconds(self):
        """Test formatting duration in seconds."""
        result = format_duration(1.5)
        assert result == "1.50s"

    def test_format_duration_milliseconds(self):
        """Test formatting duration in milliseconds."""
        result = format_duration(0.05)
        assert result == "50ms"

    def test_format_duration_zero(self):
        """Test formatting zero duration."""
        result = format_duration(0.0)
        assert result == "0ms"

    def test_format_duration_very_small(self):
        """Test formatting very small duration."""
        result = format_duration(0.001)
        assert result == "1ms"

    def test_format_duration_exactly_100ms(self):
        """Test formatting exactly 100ms (boundary case)."""
        result = format_duration(0.1)
        assert result == "0.10s"

    def test_format_duration_just_below_threshold(self):
        """Test formatting just below 100ms threshold."""
        result = format_duration(0.099)
        assert result == "99ms"

    def test_format_duration_large_value(self):
        """Test formatting large duration value."""
        result = format_duration(120.456)
        assert result == "120.46s"


class TestFormatFilePath:
    """Test format_file_path function."""

    def test_format_file_path_relative(self):
        """Test formatting relative file path."""
        result = format_file_path("src/utils/helper.py")
        assert result == "src/utils/helper.py"

    def test_format_file_path_absolute_to_cwd(self):
        """Test formatting absolute path relative to current directory."""
        cwd = Path.cwd()
        test_file = cwd / "src" / "test.py"
        result = format_file_path(str(test_file))
        assert result == "src/test.py"

    def test_format_file_path_with_base_path(self):
        """Test formatting absolute path with custom base path."""
        # Use Windows-style paths for consistent testing on Windows
        base_path = Path("C:/Users/user/project")
        test_file = base_path / "src" / "main.py"
        result = format_file_path(str(test_file), base_path)
        assert result == "src/main.py"

    def test_format_file_path_with_backslashes(self):
        """Test formatting path with backslashes (Windows)."""
        result = format_file_path(r"src\utils\helper.py")
        assert result == "src/utils/helper.py"

    def test_format_file_path_not_relative_to_base(self):
        """Test formatting path not relative to base path."""
        base_path = Path("/home/user/project")
        file_path = "/other/location/file.py"
        result = format_file_path(file_path, base_path)
        # Should return as-is with forward slashes
        assert result == "/other/location/file.py"

    def test_format_file_path_windows_absolute_not_relative(self):
        """Test formatting Windows absolute path not relative to base."""
        base_path = Path("C:/Users/user/project")
        file_path = r"D:\other\location\file.py"
        result = format_file_path(file_path, base_path)
        # Should return as-is with forward slashes
        assert result == "D:/other/location/file.py"

    def test_format_file_path_empty_string(self):
        """Test formatting empty file path."""
        result = format_file_path("")
        # Empty string becomes "." (current dir) through Path
        assert result == "."


class TestFormatIssueLocation:
    """Test format_issue_location function."""

    def test_format_issue_location_with_column(self):
        """Test formatting issue location with line and column."""
        issue = Issue(
            file_path="test.py",
            line_number=42,
            column_number=15,
            severity="error",
            message="Syntax error",
            error_code="E999",
        )
        result = format_issue_location(issue)
        assert result == "42:15"

    def test_format_issue_location_without_column(self):
        """Test formatting issue location without column."""
        issue = Issue(
            file_path="test.py",
            line_number=100,
            column_number=None,
            severity="warning",
            message="Warning message",
            error_code="W123",
        )
        result = format_issue_location(issue)
        assert result == "100"

    def test_format_issue_location_line_zero(self):
        """Test formatting issue location with line zero."""
        issue = Issue(
            file_path="test.py",
            line_number=0,
            column_number=0,
            severity="error",
            message="Error",
            error_code="E001",
        )
        result = format_issue_location(issue)
        assert result == "0:0"

    def test_format_issue_location_large_numbers(self):
        """Test formatting issue location with large numbers."""
        issue = Issue(
            file_path="test.py",
            line_number=999999,
            column_number=12345,
            severity="error",
            message="Error",
            error_code="E001",
        )
        result = format_issue_location(issue)
        assert result == "999999:12345"
