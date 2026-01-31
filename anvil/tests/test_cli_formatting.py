"""
Test CLI output formatting functions.

This module tests the formatting utilities used for console output,
including box-drawing characters, checkmarks, colors, and message formatting.
"""

import io
from pathlib import Path
from typing import List

from anvil.models.validator import Issue, ValidationResult
from anvil.reporting.console_reporter import ConsoleReporter, detect_color_support
from anvil.reporting.formatters import format_duration, format_file_path, format_issue_location
from anvil.utils.encoding import SafeChars, supports_unicode


class TestBoxDrawingCharacters:
    """Test box-drawing character rendering."""

    def test_unicode_box_characters_top_line(self):
        """Test top line of box uses correct Unicode characters."""
        chars = SafeChars(force_ascii=False)
        assert chars.box_tl == "┌"
        assert chars.box_h == "─"
        assert chars.box_tr == "┐"

    def test_unicode_box_characters_middle_line(self):
        """Test middle line of box uses correct Unicode characters."""
        chars = SafeChars(force_ascii=False)
        assert chars.box_v == "│"
        assert chars.box_lt == "├"
        assert chars.box_rt == "┤"

    def test_unicode_box_characters_bottom_line(self):
        """Test bottom line of box uses correct Unicode characters."""
        chars = SafeChars(force_ascii=False)
        assert chars.box_bl == "└"
        assert chars.box_br == "┘"

    def test_unicode_box_characters_junctions(self):
        """Test T-junction characters."""
        chars = SafeChars(force_ascii=False)
        assert chars.box_tt == "┬"
        assert chars.box_bt == "┴"
        assert chars.box_cross == "┼"

    def test_ascii_box_characters_fallback(self):
        """Test ASCII fallback for box characters."""
        chars = SafeChars(force_ascii=True)
        # All corners and junctions should use '+'
        assert chars.box_tl == "+"
        assert chars.box_tr == "+"
        assert chars.box_bl == "+"
        assert chars.box_br == "+"
        assert chars.box_lt == "+"
        assert chars.box_rt == "+"
        assert chars.box_tt == "+"
        assert chars.box_bt == "+"
        assert chars.box_cross == "+"
        # Lines
        assert chars.box_h == "-"
        assert chars.box_v == "|"


class TestCheckmarkAndCrossSymbols:
    """Test checkmark and cross symbol rendering."""

    def test_unicode_checkmark(self):
        """Test Unicode checkmark symbol."""
        chars = SafeChars(force_ascii=False)
        assert chars.check == "✓"

    def test_unicode_cross(self):
        """Test Unicode cross/X symbol."""
        chars = SafeChars(force_ascii=False)
        assert chars.cross == "✗"

    def test_ascii_checkmark_fallback(self):
        """Test ASCII fallback for checkmark."""
        chars = SafeChars(force_ascii=True)
        assert chars.check == "[PASS]"

    def test_ascii_cross_fallback(self):
        """Test ASCII fallback for cross."""
        chars = SafeChars(force_ascii=True)
        assert chars.cross == "[FAIL]"


class TestErrorWarningPrefixes:
    """Test error and warning message formatting."""

    def test_error_message_with_color(self):
        """Test error message uses red color when color enabled."""
        reporter = ConsoleReporter(use_color=True, use_unicode=True)
        issue = Issue(
            file_path="test.py",
            line_number=10,
            severity="error",
            message="Undefined variable",
        )
        stream = io.StringIO()
        reporter._print_issue(issue, stream, indent=0)
        output = stream.getvalue()

        # Should contain ANSI red color code
        assert "\033[31m" in output  # RED
        assert "error" in output.lower()
        assert "\033[0m" in output  # RESET

    def test_warning_message_with_color(self):
        """Test warning message uses yellow color when color enabled."""
        reporter = ConsoleReporter(use_color=True, use_unicode=True)
        issue = Issue(
            file_path="test.py",
            line_number=10,
            severity="warning",
            message="Unused variable",
        )
        stream = io.StringIO()
        reporter._print_issue(issue, stream, indent=0)
        output = stream.getvalue()

        # Should contain ANSI yellow color code
        assert "\033[33m" in output  # YELLOW
        assert "warning" in output.lower()
        assert "\033[0m" in output  # RESET

    def test_error_message_without_color(self):
        """Test error message without color codes when color disabled."""
        reporter = ConsoleReporter(use_color=False, use_unicode=True)
        issue = Issue(
            file_path="test.py",
            line_number=10,
            severity="error",
            message="Undefined variable",
        )
        stream = io.StringIO()
        reporter._print_issue(issue, stream, indent=0)
        output = stream.getvalue()

        # Should NOT contain ANSI color codes
        assert "\033[" not in output
        assert "error" in output.lower()


class TestANSIColorCodes:
    """Test ANSI color code usage."""

    def test_pass_status_with_green_color(self):
        """Test PASS status uses green color."""
        reporter = ConsoleReporter(use_color=True, use_unicode=True)
        result = ValidationResult(
            validator_name="flake8",
            passed=True,
            errors=[],
            warnings=[],
            files_checked=5,
            execution_time=1.2,
        )
        stream = io.StringIO()
        reporter._print_validator_results([result], stream)
        output = stream.getvalue()

        # Should contain green color code
        assert "\033[32m" in output  # GREEN
        assert "PASS" in output
        assert "\033[0m" in output  # RESET

    def test_fail_status_with_red_color(self):
        """Test FAIL status uses red color."""
        reporter = ConsoleReporter(use_color=True, use_unicode=True)
        result = ValidationResult(
            validator_name="flake8",
            passed=False,
            errors=[
                Issue(
                    file_path="test.py",
                    line_number=10,
                    severity="error",
                    message="Syntax error",
                )
            ],
            warnings=[],
            files_checked=5,
            execution_time=1.2,
        )
        stream = io.StringIO()
        reporter._print_validator_results([result], stream)
        output = stream.getvalue()

        # Should contain red color code
        assert "\033[31m" in output  # RED
        assert "FAIL" in output
        assert "\033[0m" in output  # RESET

    def test_no_color_codes_when_disabled(self):
        """Test no ANSI color codes when color disabled."""
        reporter = ConsoleReporter(use_color=False, use_unicode=True)
        result = ValidationResult(
            validator_name="flake8",
            passed=True,
            errors=[],
            warnings=[],
            files_checked=5,
            execution_time=1.2,
        )
        stream = io.StringIO()
        reporter._print_validator_results([result], stream)
        output = stream.getvalue()

        # Should NOT contain any ANSI codes
        assert "\033[" not in output
        assert "PASS" in output

    def test_color_auto_detection(self):
        """Test color support auto-detection."""
        # Just verify function runs without error
        result = detect_color_support()
        assert isinstance(result, bool)


class TestSummaryTableFormatting:
    """Test summary table formatting."""

    def test_summary_header_with_box_characters(self):
        """Test summary header uses box-drawing characters."""
        reporter = ConsoleReporter(use_color=False, use_unicode=True)
        results: List[ValidationResult] = []
        stream = io.StringIO()
        reporter.generate_report(results, stream)
        output = stream.getvalue()

        # Should contain box characters
        assert "┌" in output or "+" in output  # top-left
        assert "─" in output or "-" in output  # horizontal
        assert "┐" in output or "+" in output  # top-right

    def test_summary_contains_statistics(self):
        """Test summary contains all required statistics."""
        reporter = ConsoleReporter(use_color=False, use_unicode=True)
        results = [
            ValidationResult(
                validator_name="flake8",
                passed=True,
                errors=[],
                warnings=[],
                files_checked=5,
                execution_time=1.2,
            ),
            ValidationResult(
                validator_name="pylint",
                passed=False,
                errors=[
                    Issue(
                        file_path="test.py",
                        line_number=10,
                        severity="error",
                        message="Error",
                    )
                ],
                warnings=[],
                files_checked=3,
                execution_time=2.1,
            ),
        ]
        stream = io.StringIO()
        reporter.generate_report(results, stream)
        output = stream.getvalue()

        # Should contain statistics
        assert "Total validators:" in output
        assert "Passed:" in output
        assert "Failed:" in output
        assert "Total errors:" in output
        assert "Files checked:" in output
        assert "Execution time:" in output

    def test_summary_overall_passed_status(self):
        """Test summary shows overall passed status."""
        reporter = ConsoleReporter(use_color=False, use_unicode=True)
        results = [
            ValidationResult(
                validator_name="flake8",
                passed=True,
                errors=[],
                warnings=[],
                files_checked=5,
                execution_time=1.2,
            )
        ]
        stream = io.StringIO()
        reporter.generate_report(results, stream)
        output = stream.getvalue()

        # Should contain pass message
        assert "ALL CHECKS PASSED" in output

    def test_summary_overall_failed_status(self):
        """Test summary shows overall failed status."""
        reporter = ConsoleReporter(use_color=False, use_unicode=True)
        results = [
            ValidationResult(
                validator_name="flake8",
                passed=False,
                errors=[
                    Issue(
                        file_path="test.py",
                        line_number=10,
                        severity="error",
                        message="Error",
                    )
                ],
                warnings=[],
                files_checked=5,
                execution_time=1.2,
            )
        ]
        stream = io.StringIO()
        reporter.generate_report(results, stream)
        output = stream.getvalue()

        # Should contain fail message
        assert "VALIDATION FAILED" in output


class TestFilePathFormatting:
    """Test file path formatting and truncation."""

    def test_format_absolute_path_as_relative(self):
        """Test formatting absolute path as relative to base."""
        # Use realistic Windows path for cross-platform compatibility
        base = Path("C:/Users/user/project")
        file_path = "C:/Users/user/project/src/main.py"
        result = format_file_path(file_path, base)
        assert result == "src/main.py"

    def test_format_relative_path_unchanged(self):
        """Test relative path remains unchanged."""
        base = Path("/home/user/project")
        file_path = "src/main.py"
        result = format_file_path(file_path, base)
        assert result == "src/main.py"

    def test_format_uses_forward_slashes(self):
        """Test formatted path uses forward slashes."""
        base = Path("C:/Users/user/project")
        file_path = "C:\\Users\\user\\project\\src\\main.py"
        result = format_file_path(file_path, base)
        # Should convert backslashes to forward slashes
        assert "\\" not in result
        assert "/" in result or result == "src/main.py"

    def test_format_unrelated_path(self):
        """Test formatting path not relative to base."""
        base = Path("/home/user/project")
        file_path = "/var/log/system.log"
        result = format_file_path(file_path, base)
        # Should return path with forward slashes
        assert result == "/var/log/system.log"


class TestIssueLocationFormatting:
    """Test issue location formatting."""

    def test_format_location_with_line_and_column(self):
        """Test formatting location with both line and column."""
        issue = Issue(
            file_path="test.py",
            line_number=42,
            column_number=15,
            severity="error",
            message="Error",
        )
        result = format_issue_location(issue)
        assert result == "42:15"

    def test_format_location_with_line_only(self):
        """Test formatting location with line only."""
        issue = Issue(file_path="test.py", line_number=42, severity="error", message="Error")
        result = format_issue_location(issue)
        assert result == "42"


class TestDurationFormatting:
    """Test duration formatting."""

    def test_format_milliseconds_for_fast_execution(self):
        """Test formatting fast executions in milliseconds."""
        result = format_duration(0.05)
        assert result == "50ms"

    def test_format_seconds_with_decimals(self):
        """Test formatting slow executions in seconds."""
        result = format_duration(1.234)
        assert result == "1.23s"

    def test_format_very_fast_execution(self):
        """Test formatting very fast executions."""
        result = format_duration(0.001)
        assert result == "1ms"

    def test_format_long_execution(self):
        """Test formatting long executions."""
        result = format_duration(123.456)
        assert result == "123.46s"


class TestVerboseAndQuietModes:
    """Test verbose and quiet output modes."""

    def test_verbose_shows_rule_name(self):
        """Test verbose mode shows rule name."""
        reporter = ConsoleReporter(use_color=False, use_unicode=True, verbose=True)
        issue = Issue(
            file_path="test.py",
            line_number=10,
            severity="error",
            message="Error message",
            rule_name="E501",
        )
        stream = io.StringIO()
        reporter._print_issue(issue, stream, indent=0)
        output = stream.getvalue()

        # Should contain rule name in brackets
        assert "[E501]" in output

    def test_non_verbose_hides_rule_name(self):
        """Test non-verbose mode doesn't show extra details."""
        reporter = ConsoleReporter(use_color=False, use_unicode=True, verbose=False)
        issue = Issue(
            file_path="test.py",
            line_number=10,
            severity="error",
            message="Error message",
            rule_name="E501",
        )
        stream = io.StringIO()
        reporter._print_issue(issue, stream, indent=0)
        output = stream.getvalue()

        # Should NOT contain rule name in brackets
        assert "[E501]" not in output

    def test_quiet_mode_suppresses_warnings(self):
        """Test quiet mode suppresses warning messages."""
        reporter = ConsoleReporter(use_color=False, use_unicode=True, quiet=True)
        issue = Issue(
            file_path="test.py",
            line_number=10,
            severity="warning",
            message="Warning message",
        )
        stream = io.StringIO()
        reporter._print_issue(issue, stream, indent=0)
        output = stream.getvalue()

        # Should be empty (warning suppressed)
        assert output.strip() == ""

    def test_quiet_mode_shows_errors(self):
        """Test quiet mode still shows error messages."""
        reporter = ConsoleReporter(use_color=False, use_unicode=True, quiet=True)
        issue = Issue(
            file_path="test.py",
            line_number=10,
            severity="error",
            message="Error message",
        )
        stream = io.StringIO()
        reporter._print_issue(issue, stream, indent=0)
        output = stream.getvalue()

        # Should contain error message
        assert "Error message" in output


class TestUnicodeSupport:
    """Test Unicode support detection."""

    def test_supports_unicode_function(self):
        """Test Unicode support detection runs without error."""
        result = supports_unicode()
        assert isinstance(result, bool)

    def test_safe_chars_auto_detection(self):
        """Test SafeChars auto-detects Unicode support."""
        chars = SafeChars(force_ascii=None)
        # Should return either Unicode or ASCII characters
        check = chars.check
        assert check in ("✓", "[PASS]")
