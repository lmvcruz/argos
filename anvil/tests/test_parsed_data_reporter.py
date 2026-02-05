"""
Tests for parsed_data_reporter module.

Tests the ParsedDataReporter class for generating validation result reports.
"""

import json
from io import StringIO
from unittest.mock import MagicMock

import pytest

from anvil.models.validator import ValidationResult
from anvil.reporting.parsed_data_reporter import ParsedDataReporter


@pytest.fixture
def sample_validation_result():
    """Create a sample validation result."""
    result = ValidationResult(
        validator_name="test_validator",
        passed=False,
        files_checked=3,
        execution_time=1.5,
    )
    # Add some errors and warnings
    error1 = MagicMock()
    error1.error_code = "E001"
    error1.file_path = "file1.py"
    error1.line_number = 10
    error1.column_number = 5
    error1.message = "Test error"
    error1.severity = "error"
    error1.rule_name = "test_rule"

    warning1 = MagicMock()
    warning1.error_code = "W001"
    warning1.file_path = "file1.py"
    warning1.line_number = 20
    warning1.column_number = 10
    warning1.message = "Test warning"
    warning1.severity = "warning"
    warning1.rule_name = "test_rule2"

    result.errors = [error1]
    result.warnings = [warning1]

    return result


class TestParsedDataReporter:
    """Test ParsedDataReporter class."""

    def test_reporter_creation(self):
        """Test creating a reporter with default indentation."""
        reporter = ParsedDataReporter()
        assert reporter.indent == 2

    def test_reporter_custom_indentation(self):
        """Test creating a reporter with custom indentation."""
        reporter = ParsedDataReporter(indent=4)
        assert reporter.indent == 4

    def test_reporter_no_indentation(self):
        """Test creating a reporter with no indentation."""
        reporter = ParsedDataReporter(indent=None)
        assert reporter.indent is None

    def test_generate_report_single_result(self, sample_validation_result):
        """Test generating report for a single validation result."""
        reporter = ParsedDataReporter(indent=None)  # Use compact output for easier parsing
        output = StringIO()

        reporter.generate_report([sample_validation_result], output)

        output.seek(0)
        lines = [line.strip() for line in output.readlines() if line.strip()]
        assert len(lines) >= 1

        # Parse the JSON output
        parsed = json.loads(lines[0])
        assert parsed["validator"] == "test_validator"
        assert parsed["passed"] is False
        assert parsed["files_checked"] == 3
        assert parsed["execution_time"] == 1.5

    def test_generate_report_error_counts(self, sample_validation_result):
        """Test that error and warning counts are correct."""
        reporter = ParsedDataReporter(indent=None)
        output = StringIO()

        reporter.generate_report([sample_validation_result], output)

        output.seek(0)
        content = output.read().strip()
        parsed = json.loads(content)
        assert parsed["errors"] == 1
        assert parsed["warnings"] == 1
        assert parsed["total_violations"] == 2

    def test_generate_report_error_codes(self, sample_validation_result):
        """Test that error codes are counted correctly."""
        reporter = ParsedDataReporter(indent=None)
        output = StringIO()

        reporter.generate_report([sample_validation_result], output)

        output.seek(0)
        content = output.read().strip()
        parsed = json.loads(content)
        assert "by_code" in parsed
        assert parsed["by_code"]["E001"] == 1
        assert parsed["by_code"]["W001"] == 1

    def test_generate_report_file_violations(self, sample_validation_result):
        """Test that file violations are structured correctly."""
        reporter = ParsedDataReporter(indent=None)
        output = StringIO()

        reporter.generate_report([sample_validation_result], output)

        output.seek(0)
        content = output.read().strip()
        parsed = json.loads(content)
        assert "file_violations" in parsed
        assert "file1.py" in parsed["file_violations"]

        violations = parsed["file_violations"]["file1.py"]
        assert len(violations) == 2

        # Check first violation (error)
        error_violation = violations[0]
        assert error_violation["line"] == 10
        assert error_violation["column"] == 5
        assert error_violation["code"] == "E001"
        assert error_violation["message"] == "Test error"
        assert error_violation["severity"] == "error"
        assert error_violation["rule"] == "test_rule"

    def test_generate_report_multiple_results(self):
        """Test generating report for multiple validation results."""
        reporter = ParsedDataReporter(indent=None)
        output = StringIO()

        result1 = ValidationResult(
            validator_name="validator1", passed=True, files_checked=2, execution_time=0.5
        )
        result2 = ValidationResult(
            validator_name="validator2", passed=False, files_checked=3, execution_time=1.0
        )

        reporter.generate_report([result1, result2], output)

        output.seek(0)
        content = output.read().strip()
        # When indent=None, JSON output is on a single line per result
        lines = content.split("\n")
        assert len(lines) >= 2

        parsed1 = json.loads(lines[0])
        parsed2 = json.loads(lines[1])

        assert parsed1["validator"] == "validator1"
        assert parsed2["validator"] == "validator2"

    def test_generate_report_no_violations(self):
        """Test report generation for result with no violations."""
        reporter = ParsedDataReporter(indent=None)
        output = StringIO()

        result = ValidationResult(
            validator_name="clean_validator", passed=True, files_checked=5, execution_time=0.2
        )
        result.errors = []
        result.warnings = []

        reporter.generate_report([result], output)

        output.seek(0)
        content = output.read().strip()
        parsed = json.loads(content)
        assert parsed["passed"] is True
        assert parsed["errors"] == 0
        assert parsed["warnings"] == 0
        assert "file_violations" not in parsed

    def test_generate_report_no_output_stream(self, sample_validation_result, capsys):
        """Test that report is written to stdout when no stream provided."""
        reporter = ParsedDataReporter(indent=None)
        reporter.generate_report([sample_validation_result])

        captured = capsys.readouterr()
        assert captured.out  # Should have output
        content = captured.out.strip()
        parsed = json.loads(content)
        assert parsed["validator"] == "test_validator"

    def test_result_to_parsed_dict_basic(self):
        """Test basic conversion of ValidationResult to parsed dict."""
        reporter = ParsedDataReporter()

        result = ValidationResult(
            validator_name="test", passed=True, files_checked=1, execution_time=0.1
        )
        result.errors = []
        result.warnings = []

        parsed = reporter._result_to_parsed_dict(result)

        assert parsed["validator"] == "test"
        assert parsed["passed"] is True
        assert parsed["files_checked"] == 1
        assert parsed["execution_time"] == 0.1
        assert parsed["errors"] == 0
        assert parsed["warnings"] == 0

    def test_result_to_parsed_dict_issue_without_rule(self):
        """Test conversion when issue doesn't have rule_name."""
        reporter = ParsedDataReporter()

        result = ValidationResult(
            validator_name="test", passed=False, files_checked=1, execution_time=0.1
        )
        issue = MagicMock()
        issue.error_code = "E001"
        issue.file_path = "test.py"
        issue.line_number = 1
        issue.column_number = 1
        issue.message = "Error"
        issue.severity = "error"
        issue.rule_name = None

        result.errors = [issue]
        result.warnings = []

        parsed = reporter._result_to_parsed_dict(result)

        violation = parsed["file_violations"]["test.py"][0]
        assert "rule" not in violation
