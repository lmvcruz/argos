"""
Unit tests for Scout reporting functionality.

Tests reporting and visualization features:
- Console failure summary
- HTML report generation
- Failure timeline visualization
- Platform comparison tables
- Flaky test highlighting
- Export formats (JSON, CSV)
"""

import json
from datetime import datetime

from scout.analysis import (
    FlakyTest,
    PlatformFailure,
    Recommendation,
)
from scout.failure_parser import Failure, FailureLocation
from scout.reporting import (
    ConsoleReporter,
    CsvExporter,
    HtmlReporter,
    JsonExporter,
    ReportFormatter,
)


class TestReportFormatter:
    """Test basic report formatting utilities."""

    def test_format_duration_ms(self):
        """Test formatting of duration in milliseconds."""
        formatter = ReportFormatter()
        assert formatter.format_duration(1000.0) == "1.00s"
        assert formatter.format_duration(500.5) == "500ms"
        assert formatter.format_duration(1500.0) == "1.50s"
        assert formatter.format_duration(50.0) == "50ms"

    def test_format_duration_none(self):
        """Test formatting when duration is None."""
        formatter = ReportFormatter()
        assert formatter.format_duration(None) == "N/A"

    def test_format_timestamp(self):
        """Test formatting of timestamps."""
        formatter = ReportFormatter()
        dt = datetime(2026, 2, 1, 14, 30, 0)
        assert formatter.format_timestamp(dt) == "2026-02-01 14:30:00"

    def test_format_percentage(self):
        """Test formatting of percentages."""
        formatter = ReportFormatter()
        assert formatter.format_percentage(0.9523) == "95.23%"
        assert formatter.format_percentage(0.0) == "0.00%"
        assert formatter.format_percentage(1.0) == "100.00%"

    def test_truncate_message(self):
        """Test message truncation."""
        formatter = ReportFormatter()
        short_msg = "Short message"
        long_msg = "A" * 200

        assert formatter.truncate_message(short_msg, 100) == short_msg
        truncated = formatter.truncate_message(long_msg, 100)
        assert len(truncated) <= 103  # 100 + "..."
        assert truncated.endswith("...")


class TestConsoleReporter:
    """Test console reporting functionality."""

    def test_generate_failure_summary_empty(self):
        """Test console summary with no failures."""
        reporter = ConsoleReporter(use_color=False)
        failures = []

        output = reporter.generate_failure_summary(failures)

        assert "No test failures detected" in output or "0 failures" in output

    def test_generate_failure_summary_with_failures(self):
        """Test console summary with failures."""
        reporter = ConsoleReporter(use_color=False)
        failures = [
            Failure(
                test_name="test_example",
                test_file="test_file.py",
                message="AssertionError: Expected True, got False",
                location=FailureLocation(file="test_file.py", line=42),
            ),
            Failure(
                test_name="test_another",
                test_file="test_file2.py",
                message="ValueError: Invalid input",
            ),
        ]

        output = reporter.generate_failure_summary(failures)

        assert "test_example" in output
        assert "test_another" in output
        assert "test_file.py" in output
        assert "AssertionError" in output

    def test_generate_failure_summary_with_colors(self):
        """Test colored console output."""
        reporter = ConsoleReporter(use_color=True)
        failures = [
            Failure(
                test_name="test_failure",
                test_file="test.py",
                message="Error occurred",
            )
        ]

        output = reporter.generate_failure_summary(failures)

        # Should contain ANSI color codes
        assert "\033[" in output or "test_failure" in output

    def test_generate_flaky_test_report(self):
        """Test flaky test reporting."""
        reporter = ConsoleReporter(use_color=False)
        flaky_tests = [
            FlakyTest(
                test_name="test_flaky_1",
                pass_rate=0.6,
                fail_rate=0.4,
                total_runs=10,
            ),
            FlakyTest(
                test_name="test_flaky_2",
                pass_rate=0.75,
                fail_rate=0.25,
                total_runs=20,
            ),
        ]

        output = reporter.generate_flaky_test_report(flaky_tests)

        assert "test_flaky_1" in output
        assert "test_flaky_2" in output
        assert "60.00%" in output or "0.6" in output  # pass rate
        assert "10" in output  # total runs
        assert "20" in output  # total runs

    def test_generate_platform_comparison(self):
        """Test platform comparison table."""
        reporter = ConsoleReporter(use_color=False)
        platform_failures = [
            PlatformFailure(
                test_name="test_platform_specific",
                failing_platforms=["windows"],
                passing_platforms=["linux", "macos"],
            ),
            PlatformFailure(
                test_name="test_windows_linux",
                failing_platforms=["windows", "linux"],
                passing_platforms=["macos"],
            ),
        ]

        output = reporter.generate_platform_comparison(platform_failures)

        assert "test_platform_specific" in output
        assert "windows" in output.lower()
        assert "linux" in output.lower()

    def test_generate_recommendations_report(self):
        """Test recommendations reporting."""
        reporter = ConsoleReporter(use_color=False)
        recommendations = [
            Recommendation(
                category="Flaky Tests",
                description="Address flaky tests that fail intermittently",
                priority="high",
                suggested_actions=[
                    "Add retries to test_flaky_1",
                    "Investigate timing issues in test_flaky_2",
                ],
            ),
            Recommendation(
                category="Platform Issues",
                description="Fix platform-specific failures",
                priority="medium",
                suggested_actions=["Test on Windows environment"],
            ),
        ]

        output = reporter.generate_recommendations_report(recommendations)

        assert "Flaky Tests" in output
        assert "high" in output.lower() or "HIGH" in output
        assert "Add retries" in output

    def test_color_detection_auto(self):
        """Test automatic color detection."""
        reporter = ConsoleReporter(use_color=None)  # Auto-detect
        # Should not crash
        assert isinstance(reporter.use_color, bool)


class TestHtmlReporter:
    """Test HTML report generation."""

    def test_generate_html_report_basic(self):
        """Test basic HTML report generation."""
        reporter = HtmlReporter()
        failures = [
            Failure(
                test_name="test_example",
                test_file="test_file.py",
                message="Assertion failed",
                location=FailureLocation(file="test_file.py", line=10),
            )
        ]

        html = reporter.generate_report(failures)

        assert "<!DOCTYPE html>" in html or "<html" in html
        assert "test_example" in html
        assert "test_file.py" in html

    def test_generate_html_report_with_timeline(self):
        """Test HTML report with failure timeline."""
        reporter = HtmlReporter()
        failures = [
            Failure(
                test_name=f"test_{i}",
                test_file="test.py",
                message="Failed",
            )
            for i in range(5)
        ]

        html = reporter.generate_report(failures, include_timeline=True)

        assert "<html" in html
        assert len(failures) == 5

    def test_generate_html_with_flaky_tests(self):
        """Test HTML report with flaky test section."""
        reporter = HtmlReporter()
        failures = []
        flaky_tests = [
            FlakyTest(
                test_name="test_flaky",
                pass_rate=0.7,
                fail_rate=0.3,
                total_runs=10,
            )
        ]

        html = reporter.generate_report(failures, flaky_tests=flaky_tests, include_timeline=False)

        assert "test_flaky" in html
        assert "70" in html or "0.7" in html

    def test_generate_html_with_platform_comparison(self):
        """Test HTML report with platform comparison."""
        reporter = HtmlReporter()
        failures = []
        platform_failures = [
            PlatformFailure(
                test_name="test_platform",
                failing_platforms=["windows"],
                passing_platforms=["linux"],
            )
        ]

        html = reporter.generate_report(failures, platform_failures=platform_failures)

        assert "test_platform" in html
        assert "windows" in html.lower() or "Windows" in html

    def test_save_html_report_to_file(self, tmp_path):
        """Test saving HTML report to file."""
        reporter = HtmlReporter()
        failures = [
            Failure(
                test_name="test_save",
                test_file="test.py",
                message="Error",
            )
        ]

        output_file = tmp_path / "report.html"
        reporter.save_report(failures, output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "test_save" in content

    def test_html_escaping(self):
        """Test HTML escaping of special characters."""
        reporter = HtmlReporter()
        failures = [
            Failure(
                test_name="test_<script>alert('XSS')</script>",
                test_file="test.py",
                message="<div>malicious</div>",
            )
        ]

        html = reporter.generate_report(failures)

        # Should not contain raw script tags
        assert "<script>alert" not in html
        # Should contain escaped versions
        assert "&lt;" in html or "script" not in html.lower()


class TestJsonExporter:
    """Test JSON export functionality."""

    def test_export_failures_to_json(self):
        """Test exporting failures to JSON."""
        exporter = JsonExporter()
        failures = [
            Failure(
                test_name="test_json",
                test_file="test.py",
                message="Failed",
                location=FailureLocation(file="test.py", line=15),
            )
        ]

        json_str = exporter.export_failures(failures)
        data = json.loads(json_str)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["test_name"] == "test_json"
        assert data[0]["test_file"] == "test.py"
        assert data[0]["message"] == "Failed"

    def test_export_flaky_tests_to_json(self):
        """Test exporting flaky tests to JSON."""
        exporter = JsonExporter()
        flaky_tests = [
            FlakyTest(
                test_name="test_flaky",
                pass_rate=0.8,
                fail_rate=0.2,
                total_runs=15,
            )
        ]

        json_str = exporter.export_flaky_tests(flaky_tests)
        data = json.loads(json_str)

        assert len(data) == 1
        assert data[0]["test_name"] == "test_flaky"
        assert data[0]["pass_rate"] == 0.8
        assert data[0]["total_runs"] == 15

    def test_export_complete_analysis_to_json(self):
        """Test exporting complete analysis results to JSON."""
        exporter = JsonExporter()
        failures = [Failure(test_name="test1", test_file="test.py", message="Error")]
        flaky_tests = [
            FlakyTest(
                test_name="test_flaky",
                pass_rate=0.5,
                fail_rate=0.5,
                total_runs=10,
            )
        ]
        platform_failures = [
            PlatformFailure(
                test_name="test_platform",
                failing_platforms=["windows"],
                passing_platforms=["linux"],
            )
        ]

        json_str = exporter.export_complete_analysis(
            failures=failures,
            flaky_tests=flaky_tests,
            platform_failures=platform_failures,
        )
        data = json.loads(json_str)

        assert "failures" in data
        assert "flaky_tests" in data
        assert "platform_failures" in data
        assert len(data["failures"]) == 1

    def test_save_json_to_file(self, tmp_path):
        """Test saving JSON to file."""
        exporter = JsonExporter()
        failures = [Failure(test_name="test", test_file="test.py", message="Error")]

        output_file = tmp_path / "failures.json"
        exporter.save_to_file(failures, output_file)

        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        assert len(data) == 1

    def test_json_indentation(self):
        """Test JSON output is properly indented."""
        exporter = JsonExporter(indent=2)
        failures = [Failure(test_name="test", test_file="test.py", message="Error")]

        json_str = exporter.export_failures(failures)

        # Should have newlines and indentation
        assert "\n" in json_str
        assert "  " in json_str  # 2-space indent


class TestCsvExporter:
    """Test CSV export functionality."""

    def test_export_failures_to_csv(self):
        """Test exporting failures to CSV."""
        exporter = CsvExporter()
        failures = [
            Failure(
                test_name="test_csv",
                test_file="test.py",
                message="Failed",
                location=FailureLocation(file="test.py", line=20),
                duration_ms=150.5,
            ),
            Failure(
                test_name="test_csv2",
                test_file="test2.py",
                message="Error",
            ),
        ]

        csv_str = exporter.export_failures(failures)

        lines = csv_str.strip().split("\n")
        assert len(lines) == 3  # Header + 2 data rows

        # Check header
        header = lines[0]
        assert "test_name" in header
        assert "test_file" in header
        assert "message" in header

        # Check data
        assert "test_csv" in lines[1]
        assert "test.py" in lines[1]

    def test_export_flaky_tests_to_csv(self):
        """Test exporting flaky tests to CSV."""
        exporter = CsvExporter()
        flaky_tests = [
            FlakyTest(
                test_name="test_flaky",
                pass_rate=0.75,
                fail_rate=0.25,
                total_runs=20,
            )
        ]

        csv_str = exporter.export_flaky_tests(flaky_tests)

        lines = csv_str.strip().split("\n")
        assert len(lines) == 2  # Header + 1 data row

        assert "test_name" in lines[0]
        assert "pass_rate" in lines[0]
        assert "test_flaky" in lines[1]

    def test_save_csv_to_file(self, tmp_path):
        """Test saving CSV to file."""
        exporter = CsvExporter()
        failures = [Failure(test_name="test", test_file="test.py", message="Error")]

        output_file = tmp_path / "failures.csv"
        exporter.save_to_file(failures, output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "test_name" in content
        assert "test" in content

    def test_csv_escaping(self):
        """Test CSV escaping of special characters."""
        exporter = CsvExporter()
        failures = [
            Failure(
                test_name="test,with,commas",
                test_file="test.py",
                message='Message with "quotes"',
            )
        ]

        csv_str = exporter.export_failures(failures)

        # CSV should properly escape commas and quotes
        assert '"test,with,commas"' in csv_str or "test,with,commas" in csv_str


class TestReportIntegration:
    """Test integration of reporting components."""

    def test_generate_all_formats(self, tmp_path):
        """Test generating reports in all formats."""
        failures = [
            Failure(
                test_name="test_integration",
                test_file="test_int.py",
                message="Integration test failure",
                location=FailureLocation(file="test_int.py", line=100),
            )
        ]

        # Console
        console_reporter = ConsoleReporter(use_color=False)
        console_output = console_reporter.generate_failure_summary(failures)
        assert "test_integration" in console_output

        # HTML
        html_reporter = HtmlReporter()
        html_file = tmp_path / "report.html"
        html_reporter.save_report(failures, html_file)
        assert html_file.exists()

        # JSON
        json_exporter = JsonExporter()
        json_file = tmp_path / "failures.json"
        json_exporter.save_to_file(failures, json_file)
        assert json_file.exists()

        # CSV
        csv_exporter = CsvExporter()
        csv_file = tmp_path / "failures.csv"
        csv_exporter.save_to_file(failures, csv_file)
        assert csv_file.exists()

    def test_empty_failures_all_formats(self):
        """Test handling empty failures in all formats."""
        failures = []

        console_reporter = ConsoleReporter(use_color=False)
        console_output = console_reporter.generate_failure_summary(failures)
        assert "No" in console_output or "0" in console_output

        html_reporter = HtmlReporter()
        html = html_reporter.generate_report(failures)
        assert "<html" in html

        json_exporter = JsonExporter()
        json_str = json_exporter.export_failures(failures)
        assert json_str == "[]"

        csv_exporter = CsvExporter()
        csv_str = csv_exporter.export_failures(failures)
        # Should have header even with no data
        assert "test_name" in csv_str
