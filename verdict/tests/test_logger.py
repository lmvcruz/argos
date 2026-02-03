"""
Tests for verdict.logger module.

Tests TestLogger class for formatting and outputting test results.
"""

import json
from pathlib import Path

import pytest

from verdict.logger import TestLogger
from verdict.runner import TestResult


class TestTestLogger:
    """Test suite for TestLogger class."""

    def test_create_logger(self):
        """Test creating a TestLogger instance."""
        logger = TestLogger()
        assert logger is not None

    def test_log_console_single_pass(self, capsys):
        """Test logging a single passing test to console."""
        logger = TestLogger(use_color=False)

        result = TestResult("test_case_1", "suite1", True, [], None)
        logger.log_console([result])

        captured = capsys.readouterr()
        assert "test_case_1" in captured.out

    def test_log_console_single_fail(self, capsys):
        """Test logging a single failing test to console."""
        logger = TestLogger(use_color=False)

        result = TestResult(
            "test_case_2",
            "suite1",
            False,
            ["Field 'a': expected 1, got 2"],
            "Value mismatch"
        )
        logger.log_console([result])

        captured = capsys.readouterr()
        assert "test_case_2" in captured.out

    def test_log_console_with_color(self, capsys):
        """Test logging with ANSI color codes."""
        logger = TestLogger(use_color=True)

        result = TestResult("test_pass", "suite1", True, [], None)
        logger.log_console([result])

        captured = capsys.readouterr()
        assert "test_pass" in captured.out

    def test_log_console_without_color(self, capsys):
        """Test logging without color codes."""
        logger = TestLogger(use_color=False)

        result = TestResult("test_pass", "suite1", True, [], None)
        logger.log_console([result])

        captured = capsys.readouterr()
        assert "test_pass" in captured.out

    def test_log_multiple_results(self, capsys):
        """Test logging multiple test results."""
        logger = TestLogger(use_color=False)

        results = [
            TestResult("test_1", "suite1", True, [], None),
            TestResult("test_2", "suite1", False, ["Diff"], "Error"),
            TestResult("test_3", "suite1", True, [], None)
        ]

        logger.log_console(results)

        captured = capsys.readouterr()
        assert "test_1" in captured.out
        assert "test_2" in captured.out
        assert "test_3" in captured.out

    def test_export_json(self):
        """Test exporting results to JSON format."""
        logger = TestLogger()

        results = [
            TestResult("test_1", "suite1", True, [], None),
            TestResult("test_2", "suite1", False, ["Field diff"], "Value mismatch")
        ]

        json_output = logger.log_json(results)

        data = json.loads(json_output)
        assert "summary" in data
        assert "results" in data
        assert data["summary"]["total"] == 2
        assert data["summary"]["passed"] == 1
        assert data["summary"]["failed"] == 1
        assert len(data["results"]) == 2

    def test_export_json_structure(self):
        """Test JSON export has correct structure."""
        logger = TestLogger()

        results = [
            TestResult("test_1", "suite1", True, [], None)
        ]

        json_output = logger.log_json(results)
        data = json.loads(json_output)

        # Check summary structure
        assert "total" in data["summary"]
        assert "passed" in data["summary"]
        assert "failed" in data["summary"]

        # Check results structure
        assert len(data["results"]) == 1
        assert "test_name" in data["results"][0]
        assert "passed" in data["results"][0]

    def test_export_json_with_differences(self):
        """Test JSON export includes difference details."""
        logger = TestLogger()

        results = [
            TestResult(
                "test_fail",
                "suite1",
                False,
                ["Field 'a': expected 1, got 2", "Field 'b': missing"],
                "Mismatch"
            )
        ]

        json_output = logger.log_json(results)
        data = json.loads(json_output)

        test_result = data["results"][0]
        assert test_result["passed"] is False
        assert test_result["error"] == "Mismatch"
        assert "differences" in test_result
        assert len(test_result["differences"]) == 2

    def test_empty_results_summary(self, capsys):
        """Test logging summary with no results."""
        logger = TestLogger(use_color=False)

        logger.log_console([])

        captured = capsys.readouterr()
        assert "0" in captured.out

    def test_all_passing_summary(self, capsys):
        """Test logging summary with all passing tests."""
        logger = TestLogger(use_color=False)

        results = [
            TestResult("test_1", "suite1", True, [], None),
            TestResult("test_2", "suite1", True, [], None),
            TestResult("test_3", "suite1", True, [], None)
        ]

        logger.log_console(results)

        captured = capsys.readouterr()
        assert "3" in captured.out
        assert "passed" in captured.out.lower()

    def test_all_failing_summary(self, capsys):
        """Test logging summary with all failing tests."""
        logger = TestLogger(use_color=False)

        results = [
            TestResult("test_1", "suite1", False, [], "Error 1"),
            TestResult("test_2", "suite1", False, [], "Error 2")
        ]

        logger.log_console(results)

        captured = capsys.readouterr()
        assert "2" in captured.out
        assert "failed" in captured.out.lower()

    def test_mixed_results_summary(self, capsys):
        """Test logging summary with mixed pass/fail results."""
        logger = TestLogger(use_color=False)

        results = [
            TestResult("test_1", "suite1", True, [], None),
            TestResult("test_2", "suite1", False, [], "Error"),
            TestResult("test_3", "suite1", True, [], None),
            TestResult("test_4", "suite1", False, [], "Error"),
            TestResult("test_5", "suite1", True, [], None)
        ]

        logger.log_console(results)

        captured = capsys.readouterr()
        assert "5" in captured.out  # Total
        assert "3" in captured.out  # Passed
        assert "2" in captured.out  # Failed

    def test_json_export_formatting(self):
        """Test that JSON export is properly formatted."""
        logger = TestLogger()

        results = [TestResult("test", "suite1", True, [], None)]
        json_output = logger.log_json(results)

        # Read and verify it's valid JSON
        data = json.loads(json_output)  # Should not raise

        assert isinstance(data, dict)

    def test_error_status_in_results(self, capsys):
        """Test logging results with error."""
        logger = TestLogger(use_color=False)

        result = TestResult("test_error", "suite1", False, [], "Execution failed")
        logger.log_console([result])

        captured = capsys.readouterr()
        assert "Execution failed" in captured.out
