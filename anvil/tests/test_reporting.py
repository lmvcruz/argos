"""
Tests for result aggregation and reporting.

This module tests the generation of console and JSON reports from
validation results, including colored output, verbosity levels, and
various output formats.
"""

import json
import sys
from io import StringIO
from pathlib import Path
from typing import List

import pytest

from anvil.models.validator import Issue, ValidationResult
from anvil.reporting.console_reporter import ConsoleReporter
from anvil.reporting.json_reporter import JSONReporter
from anvil.reporting.reporter import ReportSummary


@pytest.fixture
def passing_results() -> List[ValidationResult]:
    """Create a list of passing validation results."""
    return [
        ValidationResult(
            validator_name="flake8",
            passed=True,
            errors=[],
            warnings=[],
            files_checked=10,
            execution_time=1.5,
        ),
        ValidationResult(
            validator_name="black",
            passed=True,
            errors=[],
            warnings=[],
            files_checked=10,
            execution_time=0.8,
        ),
        ValidationResult(
            validator_name="isort",
            passed=True,
            errors=[],
            warnings=[],
            files_checked=10,
            execution_time=0.5,
        ),
    ]


@pytest.fixture
def failing_results() -> List[ValidationResult]:
    """Create a list of validation results with failures."""
    return [
        ValidationResult(
            validator_name="flake8",
            passed=False,
            errors=[
                Issue(
                    file_path="src/main.py",
                    line_number=10,
                    message="E501 line too long (120 > 100 characters)",
                    severity="error",
                    column_number=101,
                    rule_name="E501",
                ),
                Issue(
                    file_path="src/utils.py",
                    line_number=25,
                    message="F401 'os' imported but unused",
                    severity="error",
                    rule_name="F401",
                ),
            ],
            warnings=[
                Issue(
                    file_path="src/main.py",
                    line_number=15,
                    message="W503 line break before binary operator",
                    severity="warning",
                    rule_name="W503",
                ),
            ],
            files_checked=10,
            execution_time=1.5,
        ),
        ValidationResult(
            validator_name="black",
            passed=False,
            errors=[
                Issue(
                    file_path="src/main.py",
                    line_number=0,
                    message="File would be reformatted",
                    severity="error",
                ),
            ],
            warnings=[],
            files_checked=10,
            execution_time=0.8,
        ),
        ValidationResult(
            validator_name="isort",
            passed=True,
            errors=[],
            warnings=[],
            files_checked=10,
            execution_time=0.5,
        ),
    ]


@pytest.fixture
def mixed_results() -> List[ValidationResult]:
    """Create a list with mixed pass/fail results and multiple issue types."""
    return [
        ValidationResult(
            validator_name="pylint",
            passed=False,
            errors=[
                Issue(
                    file_path="src/module.py",
                    line_number=42,
                    column_number=10,
                    message="C0103: Variable name doesn't conform to snake_case",
                    severity="error",
                    rule_name="C0103",
                ),
            ],
            warnings=[
                Issue(
                    file_path="src/module.py",
                    line_number=50,
                    message="R0913: Too many arguments (6/5)",
                    severity="warning",
                    rule_name="R0913",
                ),
            ],
            files_checked=5,
            execution_time=3.2,
        ),
        ValidationResult(
            validator_name="black",
            passed=True,
            errors=[],
            warnings=[],
            files_checked=5,
            execution_time=0.4,
        ),
    ]


class TestReportSummary:
    """Test report summary generation."""

    def test_summary_from_passing_results(self, passing_results):
        """Test creating summary from all passing results."""
        summary = ReportSummary.from_results(passing_results)

        assert summary.total_validators == 3
        assert summary.passed_validators == 3
        assert summary.failed_validators == 0
        assert summary.total_errors == 0
        assert summary.total_warnings == 0
        assert summary.total_files_checked == 30
        assert summary.overall_passed is True
        assert summary.total_execution_time == pytest.approx(2.8, rel=0.1)

    def test_summary_from_failing_results(self, failing_results):
        """Test creating summary from results with failures."""
        summary = ReportSummary.from_results(failing_results)

        assert summary.total_validators == 3
        assert summary.passed_validators == 1
        assert summary.failed_validators == 2
        assert summary.total_errors == 3
        assert summary.total_warnings == 1
        assert summary.total_files_checked == 30
        assert summary.overall_passed is False

    def test_summary_with_empty_results(self):
        """Test creating summary from empty results list."""
        summary = ReportSummary.from_results([])

        assert summary.total_validators == 0
        assert summary.passed_validators == 0
        assert summary.failed_validators == 0
        assert summary.total_errors == 0
        assert summary.total_warnings == 0
        assert summary.overall_passed is True

    def test_summary_to_dict(self, passing_results):
        """Test converting summary to dictionary."""
        summary = ReportSummary.from_results(passing_results)
        data = summary.to_dict()

        assert data["total_validators"] == 3
        assert data["passed_validators"] == 3
        assert data["failed_validators"] == 0
        assert data["overall_passed"] is True
        assert "total_execution_time" in data


class TestConsoleReporter:
    """Test console report generation."""

    def test_generate_report_all_passing(self, passing_results):
        """Test console report with all validators passing."""
        reporter = ConsoleReporter(use_color=False)
        output = StringIO()
        reporter.generate_report(passing_results, output_stream=output)

        report = output.getvalue()
        assert "✓" in report or "PASS" in report
        assert "flake8" in report
        assert "black" in report
        assert "isort" in report

    def test_generate_report_with_failures(self, failing_results):
        """Test console report with failures."""
        reporter = ConsoleReporter(use_color=False)
        output = StringIO()
        reporter.generate_report(failing_results, output_stream=output)

        report = output.getvalue()
        assert "E501 line too long" in report
        assert "F401 'os' imported but unused" in report
        assert "src/main.py" in report
        assert "src/utils.py" in report
        assert "✗" in report or "FAIL" in report

    def test_report_includes_execution_times(self, passing_results):
        """Test that report shows validator execution times."""
        reporter = ConsoleReporter(use_color=False)
        output = StringIO()
        reporter.generate_report(passing_results, output_stream=output)

        report = output.getvalue()
        assert "1.5" in report or "1.50" in report  # flake8 time
        assert "0.8" in report or "0.80" in report  # black time

    def test_report_shows_overall_pass_fail(self, failing_results):
        """Test that report shows overall pass/fail status."""
        reporter = ConsoleReporter(use_color=False)
        output = StringIO()
        reporter.generate_report(failing_results, output_stream=output)

        report = output.getvalue()
        assert "FAIL" in report or "Failed" in report

    def test_report_groups_issues_by_file(self, failing_results):
        """Test that issues are grouped by file."""
        reporter = ConsoleReporter(use_color=False)
        output = StringIO()
        reporter.generate_report(failing_results, output_stream=output)

        report = output.getvalue()
        # Check that file paths appear as headers
        assert "src/main.py" in report
        assert "src/utils.py" in report

    def test_report_groups_issues_by_validator(self, failing_results):
        """Test that issues can be grouped by validator."""
        reporter = ConsoleReporter(use_color=False, group_by="validator")
        output = StringIO()
        reporter.generate_report(failing_results, output_stream=output)

        report = output.getvalue()
        assert "flake8" in report
        assert "black" in report

    def test_report_shows_summary_statistics(self, failing_results):
        """Test that report includes summary statistics."""
        reporter = ConsoleReporter(use_color=False)
        output = StringIO()
        reporter.generate_report(failing_results, output_stream=output)

        report = output.getvalue()
        assert "3" in report  # total validators
        assert "2" in report  # failed validators
        assert "30" in report  # files checked

    def test_colored_output_enabled(self, passing_results):
        """Test that colored output includes ANSI codes when enabled."""
        reporter = ConsoleReporter(use_color=True)
        output = StringIO()
        reporter.generate_report(passing_results, output_stream=output)

        report = output.getvalue()
        # Check for ANSI color codes
        assert "\033[" in report

    def test_plain_text_output(self, passing_results):
        """Test that plain text output has no ANSI codes."""
        reporter = ConsoleReporter(use_color=False)
        output = StringIO()
        reporter.generate_report(passing_results, output_stream=output)

        report = output.getvalue()
        # Should not contain ANSI escape sequences
        assert "\033[" not in report

    def test_verbose_mode_includes_all_details(self, failing_results):
        """Test that verbose mode shows all issue details."""
        reporter = ConsoleReporter(use_color=False, verbose=True)
        output = StringIO()
        reporter.generate_report(failing_results, output_stream=output)

        report = output.getvalue()
        # Should include column numbers, rule names, etc.
        assert "E501" in report
        assert "F401" in report
        assert "column" in report.lower() or "101" in report

    def test_quiet_mode_shows_only_errors(self, failing_results):
        """Test that quiet mode suppresses warnings."""
        reporter = ConsoleReporter(use_color=False, quiet=True)
        output = StringIO()
        reporter.generate_report(failing_results, output_stream=output)

        report = output.getvalue()
        # Should show errors but not warnings
        assert "E501" in report
        assert "W503" not in report

    def test_report_with_box_drawing_characters(self, passing_results):
        """Test that report uses box-drawing characters."""
        reporter = ConsoleReporter(use_color=False, use_unicode=True)
        output = StringIO()
        reporter.generate_report(passing_results, output_stream=output)

        report = output.getvalue()
        # Check for box-drawing characters
        has_box_chars = any(char in report for char in ["─", "│", "┌", "┐", "└", "┘", "├", "┤"])
        assert has_box_chars

    def test_report_without_box_drawing(self, passing_results):
        """Test that report can use ASCII-only characters."""
        reporter = ConsoleReporter(use_color=False, use_unicode=False)
        output = StringIO()
        reporter.generate_report(passing_results, output_stream=output)

        report = output.getvalue()
        # Should use ASCII alternatives
        assert "-" in report or "=" in report

    def test_empty_results_report(self):
        """Test report generation with empty results."""
        reporter = ConsoleReporter(use_color=False)
        output = StringIO()
        reporter.generate_report([], output_stream=output)

        report = output.getvalue()
        assert "No validators" in report or "0" in report


class TestJSONReporter:
    """Test JSON report generation."""

    def test_generate_json_report_all_passing(self, passing_results):
        """Test JSON report with all validators passing."""
        reporter = JSONReporter()
        output = StringIO()
        reporter.generate_report(passing_results, output_stream=output)

        data = json.loads(output.getvalue())
        assert data["summary"]["overall_passed"] is True
        assert data["summary"]["total_validators"] == 3
        assert len(data["results"]) == 3

    def test_generate_json_report_with_failures(self, failing_results):
        """Test JSON report with failures."""
        reporter = JSONReporter()
        output = StringIO()
        reporter.generate_report(failing_results, output_stream=output)

        data = json.loads(output.getvalue())
        assert data["summary"]["overall_passed"] is False
        assert data["summary"]["failed_validators"] == 2
        assert data["summary"]["total_errors"] == 3

    def test_json_report_includes_all_errors(self, failing_results):
        """Test that JSON report includes all error details."""
        reporter = JSONReporter()
        output = StringIO()
        reporter.generate_report(failing_results, output_stream=output)

        data = json.loads(output.getvalue())
        flake8_result = next(r for r in data["results"] if r["validator_name"] == "flake8")
        assert len(flake8_result["errors"]) == 2
        assert flake8_result["errors"][0]["message"] == "E501 line too long (120 > 100 characters)"

    def test_json_report_includes_warnings(self, failing_results):
        """Test that JSON report includes warnings."""
        reporter = JSONReporter()
        output = StringIO()
        reporter.generate_report(failing_results, output_stream=output)

        data = json.loads(output.getvalue())
        flake8_result = next(r for r in data["results"] if r["validator_name"] == "flake8")
        assert len(flake8_result["warnings"]) == 1

    def test_json_report_includes_execution_times(self, passing_results):
        """Test that JSON report includes execution times."""
        reporter = JSONReporter()
        output = StringIO()
        reporter.generate_report(passing_results, output_stream=output)

        data = json.loads(output.getvalue())
        assert "total_execution_time" in data["summary"]
        for result in data["results"]:
            assert "execution_time" in result

    def test_json_report_includes_file_counts(self, passing_results):
        """Test that JSON report includes file counts."""
        reporter = JSONReporter()
        output = StringIO()
        reporter.generate_report(passing_results, output_stream=output)

        data = json.loads(output.getvalue())
        assert data["summary"]["total_files_checked"] == 30
        for result in data["results"]:
            assert result["files_checked"] == 10

    def test_json_report_structure(self, mixed_results):
        """Test that JSON report has correct structure."""
        reporter = JSONReporter()
        output = StringIO()
        reporter.generate_report(mixed_results, output_stream=output)

        data = json.loads(output.getvalue())
        assert "summary" in data
        assert "results" in data
        assert "timestamp" in data
        assert isinstance(data["results"], list)

    def test_json_report_with_indent(self, passing_results):
        """Test that JSON can be pretty-printed."""
        reporter = JSONReporter(indent=2)
        output = StringIO()
        reporter.generate_report(passing_results, output_stream=output)

        json_str = output.getvalue()
        # Pretty-printed JSON should have newlines and indentation
        assert "\n" in json_str
        assert "  " in json_str

    def test_json_report_without_indent(self, passing_results):
        """Test that JSON can be compact."""
        reporter = JSONReporter(indent=None)
        output = StringIO()
        reporter.generate_report(passing_results, output_stream=output)

        json_str = output.getvalue()
        # Compact JSON should be single line
        lines = json_str.strip().split("\n")
        assert len(lines) == 1

    def test_json_report_file_export(self, passing_results, tmp_path):
        """Test exporting JSON report to file."""
        reporter = JSONReporter()
        output_file = tmp_path / "report.json"

        with open(output_file, "w") as f:
            reporter.generate_report(passing_results, output_stream=f)

        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        assert data["summary"]["overall_passed"] is True

    def test_json_report_empty_results(self):
        """Test JSON report with empty results."""
        reporter = JSONReporter()
        output = StringIO()
        reporter.generate_report([], output_stream=output)

        data = json.loads(output.getvalue())
        assert data["summary"]["total_validators"] == 0
        assert data["results"] == []


class TestReportFormatting:
    """Test report formatting utilities."""

    def test_format_duration_seconds(self):
        """Test duration formatting in seconds."""
        from anvil.reporting.formatters import format_duration

        assert format_duration(1.5) == "1.50s"
        assert format_duration(0.123) == "0.12s"

    def test_format_duration_milliseconds(self):
        """Test duration formatting in milliseconds for small values."""
        from anvil.reporting.formatters import format_duration

        assert format_duration(0.001) == "1ms"
        assert format_duration(0.0123) == "12ms"

    def test_format_file_path_relative(self):
        """Test file path formatting with relative paths."""
        from anvil.reporting.formatters import format_file_path

        result = format_file_path("src/main.py", base_path=Path("/project"))
        assert result == "src/main.py"

    def test_format_file_path_absolute(self):
        """Test file path formatting with absolute paths."""
        from anvil.reporting.formatters import format_file_path

        # Use platform-appropriate absolute paths
        if sys.platform == "win32":
            base = Path("C:/project")
            abs_path = "C:/project/src/main.py"
        else:
            base = Path("/project")
            abs_path = "/project/src/main.py"

        result = format_file_path(abs_path, base_path=base)
        assert result == "src/main.py"

    def test_format_issue_location(self):
        """Test issue location formatting."""
        from anvil.reporting.formatters import format_issue_location

        issue = Issue(
            file_path="src/main.py",
            line_number=42,
            column_number=10,
            message="Test error",
            severity="error",
        )
        location = format_issue_location(issue)
        assert "42" in location
        assert "10" in location

    def test_format_issue_location_without_column(self):
        """Test issue location formatting without column."""
        from anvil.reporting.formatters import format_issue_location

        issue = Issue(
            file_path="src/main.py",
            line_number=42,
            message="Test error",
            severity="error",
        )
        location = format_issue_location(issue)
        assert "42" in location
        assert ":" not in location or location.count(":") == 1


class TestColorSupport:
    """Test color support detection."""

    def test_detect_color_support_tty(self, monkeypatch):
        """Test color support detection with TTY."""
        from anvil.reporting.console_reporter import detect_color_support

        # Mock isatty to return True
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)
        assert detect_color_support() is True

    def test_detect_color_support_no_tty(self, monkeypatch):
        """Test color support detection without TTY."""
        from anvil.reporting.console_reporter import detect_color_support

        # Mock isatty to return False
        monkeypatch.setattr("sys.stdout.isatty", lambda: False)
        assert detect_color_support() is False

    def test_detect_color_support_no_color_env(self, monkeypatch):
        """Test that NO_COLOR environment variable disables color."""
        from anvil.reporting.console_reporter import detect_color_support

        monkeypatch.setenv("NO_COLOR", "1")
        assert detect_color_support() is False


class TestReportExport:
    """Test report file export."""

    def test_export_console_report_to_file(self, passing_results, tmp_path):
        """Test exporting console report to file."""
        reporter = ConsoleReporter(use_color=False)
        output_file = tmp_path / "report.txt"

        with open(output_file, "w", encoding="utf-8") as f:
            reporter.generate_report(passing_results, output_stream=f)

        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "flake8" in content

    def test_export_json_report_to_file(self, passing_results, tmp_path):
        """Test exporting JSON report to file."""
        reporter = JSONReporter()
        output_file = tmp_path / "report.json"

        with open(output_file, "w") as f:
            reporter.generate_report(passing_results, output_stream=f)

        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        assert "summary" in data


class TestIssueGrouping:
    """Test issue grouping functionality."""

    def test_group_issues_by_file(self, failing_results):
        """Test grouping issues by file path."""
        from anvil.reporting.grouping import group_issues_by_file

        grouped = group_issues_by_file(failing_results)
        assert "src/main.py" in grouped
        assert "src/utils.py" in grouped
        assert len(grouped["src/main.py"]) == 3  # 2 errors + 1 warning

    def test_group_issues_by_validator(self, failing_results):
        """Test grouping issues by validator name."""
        from anvil.reporting.grouping import group_issues_by_validator

        grouped = group_issues_by_validator(failing_results)
        assert "flake8" in grouped
        assert "black" in grouped
        assert len(grouped["flake8"]) == 3  # 2 errors + 1 warning

    def test_group_issues_by_severity(self, failing_results):
        """Test grouping issues by severity."""
        from anvil.reporting.grouping import group_issues_by_severity

        grouped = group_issues_by_severity(failing_results)
        assert "error" in grouped
        assert "warning" in grouped
        assert len(grouped["error"]) == 3
        assert len(grouped["warning"]) == 1
