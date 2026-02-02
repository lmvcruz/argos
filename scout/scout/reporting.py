"""
Reporting and visualization for Scout.

Provides multiple output formats for test failure analysis:
- Console output with colors and formatting
- HTML reports with interactive visualizations
- JSON export for programmatic access
- CSV export for spreadsheet analysis
"""

import csv
import html
import json
import sys
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import List, Optional

from scout.analysis import FlakyTest, PlatformFailure, Recommendation
from scout.failure_parser import Failure


class ReportFormatter:
    """
    Utility class for formatting report data.

    Provides helper methods for formatting durations, timestamps,
    percentages, and messages consistently across all report types.
    """

    def format_duration(self, duration_ms: Optional[float]) -> str:
        """
        Format duration in milliseconds to human-readable string.

        Args:
            duration_ms: Duration in milliseconds, or None

        Returns:
            Formatted duration string (e.g., "1.50s", "250ms", "N/A")
        """
        if duration_ms is None:
            return "N/A"

        if duration_ms >= 1000:
            seconds = duration_ms / 1000.0
            return f"{seconds:.2f}s"
        return f"{int(duration_ms)}ms"

    def format_timestamp(self, dt: datetime) -> str:
        """
        Format timestamp to human-readable string.

        Args:
            dt: Datetime object

        Returns:
            Formatted timestamp string
        """
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def format_percentage(self, value: float) -> str:
        """
        Format percentage value.

        Args:
            value: Percentage value (0.0-1.0)

        Returns:
            Formatted percentage string (e.g., "95.23%")
        """
        return f"{value * 100:.2f}%"

    def truncate_message(self, message: str, max_length: int = 100) -> str:
        """
        Truncate long messages with ellipsis.

        Args:
            message: Message to truncate
            max_length: Maximum length before truncation

        Returns:
            Truncated message with "..." if needed
        """
        if len(message) <= max_length:
            return message
        return message[: max_length - 3] + "..."


class ConsoleReporter:
    """
    Console reporter for test failure analysis.

    Generates formatted console output with optional color support
    for failure summaries, flaky test reports, platform comparisons,
    and recommendations.
    """

    # ANSI color codes
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    def __init__(self, use_color: Optional[bool] = None):
        """
        Initialize console reporter.

        Args:
            use_color: Enable color output. If None, auto-detect based on TTY
        """
        if use_color is None:
            # Auto-detect color support
            self.use_color = self._supports_color()
        else:
            self.use_color = use_color

        self.formatter = ReportFormatter()

    def _supports_color(self) -> bool:
        """
        Detect if terminal supports color output.

        Returns:
            True if colors are supported, False otherwise
        """
        # Check if output is a TTY
        if not hasattr(sys.stdout, "isatty"):
            return False
        if not sys.stdout.isatty():
            return False

        # Check NO_COLOR environment variable
        import os

        if os.environ.get("NO_COLOR"):
            return False

        return True

    def _colorize(self, text: str, color: str) -> str:
        """
        Apply color to text if colors are enabled.

        Args:
            text: Text to colorize
            color: ANSI color code

        Returns:
            Colored text or plain text if colors disabled
        """
        if not self.use_color:
            return text
        return f"{color}{text}{self.RESET}"

    def generate_failure_summary(self, failures: List[Failure]) -> str:
        """
        Generate console summary of test failures.

        Args:
            failures: List of test failures

        Returns:
            Formatted console output string
        """
        output = StringIO()

        if not failures:
            output.write(self._colorize("✓ No test failures detected\n", self.GREEN))
            return output.getvalue()

        # Header
        header = f"{'=' * 70}\n"
        header += f"TEST FAILURE SUMMARY ({len(failures)} failures)\n"
        header += f"{'=' * 70}\n"
        output.write(self._colorize(header, self.BOLD))

        # Individual failures
        for idx, failure in enumerate(failures, 1):
            output.write(f"\n{idx}. ")
            output.write(self._colorize(f"{failure.test_name}\n", self.BOLD + self.RED))

            output.write(f"   File: {failure.test_file}")
            if failure.location:
                output.write(f":{failure.location.line}")
            output.write("\n")

            if failure.failure_type:
                output.write(f"   Type: {failure.failure_type}\n")

            # Truncate message for console display
            message = self.formatter.truncate_message(failure.message, 200)
            output.write(f"   Message: {message}\n")

            if failure.duration_ms:
                duration = self.formatter.format_duration(failure.duration_ms)
                output.write(f"   Duration: {duration}\n")

        output.write(f"\n{'=' * 70}\n")

        return output.getvalue()

    def generate_flaky_test_report(self, flaky_tests: List[FlakyTest]) -> str:
        """
        Generate console report for flaky tests.

        Args:
            flaky_tests: List of flaky tests detected

        Returns:
            Formatted console output string
        """
        output = StringIO()

        if not flaky_tests:
            output.write("No flaky tests detected\n")
            return output.getvalue()

        # Header
        header = f"{'=' * 70}\n"
        header += f"FLAKY TESTS ({len(flaky_tests)} detected)\n"
        header += f"{'=' * 70}\n"
        output.write(self._colorize(header, self.BOLD + self.YELLOW))

        # Table header
        output.write(f"\n{'Test Name':<40} {'Pass Rate':<12} {'Total Runs':<12}\n")
        output.write(f"{'-' * 70}\n")

        # Flaky tests
        for flaky in flaky_tests:
            pass_rate_str = self.formatter.format_percentage(flaky.pass_rate)
            output.write(
                f"{flaky.test_name:<40} " f"{pass_rate_str:<12} " f"{flaky.total_runs:<12}\n"
            )

        output.write(f"{'=' * 70}\n")

        return output.getvalue()

    def generate_platform_comparison(self, platform_failures: List[PlatformFailure]) -> str:
        """
        Generate platform comparison table.

        Args:
            platform_failures: List of platform-specific failures

        Returns:
            Formatted console output string
        """
        output = StringIO()

        if not platform_failures:
            output.write("No platform-specific failures detected\n")
            return output.getvalue()

        # Header
        header = f"{'=' * 70}\n"
        header += f"PLATFORM-SPECIFIC FAILURES ({len(platform_failures)})\n"
        header += f"{'=' * 70}\n"
        output.write(self._colorize(header, self.BOLD + self.BLUE))

        # Table
        output.write(f"\n{'Test Name':<40} {'Failing':<15} {'Passing':<15}\n")
        output.write(f"{'-' * 70}\n")

        for pf in platform_failures:
            failing = ", ".join(pf.failing_platforms)
            passing = ", ".join(pf.passing_platforms)

            output.write(f"{pf.test_name:<40} ")
            output.write(self._colorize(f"{failing:<15} ", self.RED))
            output.write(self._colorize(f"{passing:<15}\n", self.GREEN))

        output.write(f"{'=' * 70}\n")

        return output.getvalue()

    def generate_recommendations_report(self, recommendations: List[Recommendation]) -> str:
        """
        Generate actionable recommendations report.

        Args:
            recommendations: List of recommendations

        Returns:
            Formatted console output string
        """
        output = StringIO()

        if not recommendations:
            output.write("No recommendations generated\n")
            return output.getvalue()

        # Header
        header = f"{'=' * 70}\n"
        header += f"RECOMMENDATIONS ({len(recommendations)})\n"
        header += f"{'=' * 70}\n"
        output.write(self._colorize(header, self.BOLD))

        # Group by priority
        high_priority = [r for r in recommendations if r.priority == "high"]
        medium_priority = [r for r in recommendations if r.priority == "medium"]
        low_priority = [r for r in recommendations if r.priority == "low"]

        for priority_name, priority_list, color in [
            ("HIGH PRIORITY", high_priority, self.RED),
            ("MEDIUM PRIORITY", medium_priority, self.YELLOW),
            ("LOW PRIORITY", low_priority, self.BLUE),
        ]:
            if not priority_list:
                continue

            output.write(f"\n{self._colorize(priority_name, self.BOLD + color)}\n")
            output.write(f"{'-' * 70}\n")

            for rec in priority_list:
                output.write(
                    f"\n{self._colorize(rec.category, self.BOLD)}: " f"{rec.description}\n"
                )
                output.write("  Suggested actions:\n")
                for action in rec.suggested_actions:
                    output.write(f"    • {action}\n")

        output.write(f"\n{'=' * 70}\n")

        return output.getvalue()


class HtmlReporter:
    """
    HTML reporter for test failure analysis.

    Generates comprehensive HTML reports with CSS styling,
    failure summaries, flaky test highlights, platform comparisons,
    and optional timeline visualizations.
    """

    def __init__(self):
        """Initialize HTML reporter."""
        self.formatter = ReportFormatter()

    def _get_html_template(self) -> str:
        """
        Get HTML template with CSS styling.

        Returns:
            HTML template string
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scout Test Failure Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #e74c3c;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 8px;
        }}
        .failure {{
            background-color: #fff5f5;
            border-left: 4px solid #e74c3c;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .failure-header {{
            font-weight: bold;
            color: #e74c3c;
            font-size: 1.1em;
        }}
        .failure-details {{
            margin-top: 10px;
            color: #666;
        }}
        .flaky {{
            background-color: #fffbf0;
            border-left: 4px solid #f39c12;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .platform-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        .platform-table th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        .platform-table td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        .platform-fail {{
            color: #e74c3c;
        }}
        .platform-pass {{
            color: #27ae60;
        }}
        .summary {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .timestamp {{
            color: #95a5a6;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>"""

    def generate_report(
        self,
        failures: List[Failure],
        flaky_tests: Optional[List[FlakyTest]] = None,
        platform_failures: Optional[List[PlatformFailure]] = None,
        include_timeline: bool = False,
    ) -> str:
        """
        Generate HTML report.

        Args:
            failures: List of test failures
            flaky_tests: Optional list of flaky tests
            platform_failures: Optional list of platform-specific failures
            include_timeline: Include timeline visualization

        Returns:
            Complete HTML report string
        """
        content = StringIO()

        # Header
        content.write("<h1>Scout Test Failure Report</h1>\n")
        content.write(
            f'<p class="timestamp">Generated: '
            f"{self.formatter.format_timestamp(datetime.now())}</p>\n"
        )

        # Summary
        content.write('<div class="summary">\n')
        content.write("<h2>Summary</h2>\n")
        content.write(f"<p>Total Failures: {len(failures)}</p>\n")
        if flaky_tests:
            content.write(f"<p>Flaky Tests: {len(flaky_tests)}</p>\n")
        if platform_failures:
            content.write(f"<p>Platform-Specific Failures: " f"{len(platform_failures)}</p>\n")
        content.write("</div>\n")

        # Failures section
        if failures:
            content.write("<h2>Test Failures</h2>\n")
            for failure in failures:
                content.write(self._format_failure_html(failure))

        # Flaky tests section
        if flaky_tests:
            content.write("<h2>Flaky Tests</h2>\n")
            for flaky in flaky_tests:
                content.write(self._format_flaky_test_html(flaky))

        # Platform comparison section
        if platform_failures:
            content.write("<h2>Platform-Specific Failures</h2>\n")
            content.write(self._format_platform_comparison_html(platform_failures))

        # Insert content into template
        html = self._get_html_template()
        return html.format(content=content.getvalue())

    def _format_failure_html(self, failure: Failure) -> str:
        """
        Format a single failure as HTML.

        Args:
            failure: Failure object

        Returns:
            HTML string for the failure
        """
        output = StringIO()

        output.write('<div class="failure">\n')
        output.write(f'<div class="failure-header">' f"{html.escape(failure.test_name)}</div>\n")
        output.write('<div class="failure-details">\n')

        output.write(f"<strong>File:</strong> {html.escape(failure.test_file)}")
        if failure.location:
            output.write(f":{failure.location.line}")
        output.write("<br>\n")

        if failure.failure_type:
            output.write(f"<strong>Type:</strong> " f"{html.escape(failure.failure_type)}<br>\n")

        output.write(f"<strong>Message:</strong> " f"{html.escape(failure.message)}<br>\n")

        if failure.duration_ms:
            duration = self.formatter.format_duration(failure.duration_ms)
            output.write(f"<strong>Duration:</strong> {duration}<br>\n")

        output.write("</div>\n")
        output.write("</div>\n")

        return output.getvalue()

    def _format_flaky_test_html(self, flaky: FlakyTest) -> str:
        """
        Format a flaky test as HTML.

        Args:
            flaky: FlakyTest object

        Returns:
            HTML string for the flaky test
        """
        pass_rate = self.formatter.format_percentage(flaky.pass_rate)
        fail_rate = self.formatter.format_percentage(flaky.fail_rate)

        return (
            f'<div class="flaky">\n'
            f"<strong>{html.escape(flaky.test_name)}</strong><br>\n"
            f"Pass Rate: {pass_rate} | "
            f"Fail Rate: {fail_rate} | "
            f"Total Runs: {flaky.total_runs}\n"
            f"</div>\n"
        )

    def _format_platform_comparison_html(self, platform_failures: List[PlatformFailure]) -> str:
        """
        Format platform comparison as HTML table.

        Args:
            platform_failures: List of platform failures

        Returns:
            HTML string for platform comparison table
        """
        output = StringIO()

        output.write('<table class="platform-table">\n')
        output.write("<thead>\n")
        output.write(
            "<tr><th>Test Name</th>"
            "<th>Failing Platforms</th>"
            "<th>Passing Platforms</th></tr>\n"
        )
        output.write("</thead>\n")
        output.write("<tbody>\n")

        for pf in platform_failures:
            failing = html.escape(", ".join(pf.failing_platforms))
            passing = html.escape(", ".join(pf.passing_platforms))

            output.write("<tr>\n")
            output.write(f"<td>{html.escape(pf.test_name)}</td>\n")
            output.write(f'<td class="platform-fail">{failing}</td>\n')
            output.write(f'<td class="platform-pass">{passing}</td>\n')
            output.write("</tr>\n")

        output.write("</tbody>\n")
        output.write("</table>\n")

        return output.getvalue()

    def save_report(
        self,
        failures: List[Failure],
        output_file: Path,
        flaky_tests: Optional[List[FlakyTest]] = None,
        platform_failures: Optional[List[PlatformFailure]] = None,
    ) -> None:
        """
        Generate and save HTML report to file.

        Args:
            failures: List of test failures
            output_file: Output file path
            flaky_tests: Optional list of flaky tests
            platform_failures: Optional list of platform-specific failures
        """
        html = self.generate_report(failures, flaky_tests, platform_failures)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)


class JsonExporter:
    """
    JSON exporter for test failure data.

    Exports failure analysis results to JSON format for
    programmatic consumption or integration with other tools.
    """

    def __init__(self, indent: Optional[int] = 2):
        """
        Initialize JSON exporter.

        Args:
            indent: Indentation level for JSON output (None for compact)
        """
        self.indent = indent

    def export_failures(self, failures: List[Failure]) -> str:
        """
        Export failures to JSON string.

        Args:
            failures: List of failures

        Returns:
            JSON string representation
        """
        data = []

        for failure in failures:
            failure_dict = {
                "test_name": failure.test_name,
                "test_file": failure.test_file,
                "message": failure.message,
            }

            if failure.location:
                failure_dict["location"] = {
                    "file": failure.location.file,
                    "line": failure.location.line,
                }
                if failure.location.column:
                    failure_dict["location"]["column"] = failure.location.column
                if failure.location.function:
                    failure_dict["location"]["function"] = failure.location.function

            if failure.failure_type:
                failure_dict["failure_type"] = failure.failure_type

            if failure.duration_ms is not None:
                failure_dict["duration_ms"] = failure.duration_ms

            data.append(failure_dict)

        return json.dumps(data, indent=self.indent)

    def export_flaky_tests(self, flaky_tests: List[FlakyTest]) -> str:
        """
        Export flaky tests to JSON string.

        Args:
            flaky_tests: List of flaky tests

        Returns:
            JSON string representation
        """
        data = [
            {
                "test_name": flaky.test_name,
                "pass_rate": flaky.pass_rate,
                "fail_rate": flaky.fail_rate,
                "total_runs": flaky.total_runs,
            }
            for flaky in flaky_tests
        ]

        return json.dumps(data, indent=self.indent)

    def export_complete_analysis(
        self,
        failures: List[Failure],
        flaky_tests: Optional[List[FlakyTest]] = None,
        platform_failures: Optional[List[PlatformFailure]] = None,
        recommendations: Optional[List[Recommendation]] = None,
    ) -> str:
        """
        Export complete analysis to JSON string.

        Args:
            failures: List of failures
            flaky_tests: Optional list of flaky tests
            platform_failures: Optional list of platform failures
            recommendations: Optional list of recommendations

        Returns:
            JSON string with all analysis data
        """
        data = {
            "failures": json.loads(self.export_failures(failures)),
        }

        if flaky_tests:
            data["flaky_tests"] = json.loads(self.export_flaky_tests(flaky_tests))

        if platform_failures:
            data["platform_failures"] = [
                {
                    "test_name": pf.test_name,
                    "failing_platforms": pf.failing_platforms,
                    "passing_platforms": pf.passing_platforms,
                }
                for pf in platform_failures
            ]

        if recommendations:
            data["recommendations"] = [
                {
                    "category": rec.category,
                    "description": rec.description,
                    "priority": rec.priority,
                    "suggested_actions": rec.suggested_actions,
                }
                for rec in recommendations
            ]

        return json.dumps(data, indent=self.indent)

    def save_to_file(self, failures: List[Failure], output_file: Path) -> None:
        """
        Save failures to JSON file.

        Args:
            failures: List of failures
            output_file: Output file path
        """
        json_str = self.export_failures(failures)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(json_str)


class CsvExporter:
    """
    CSV exporter for test failure data.

    Exports failure data to CSV format for spreadsheet analysis
    or integration with data analysis tools.
    """

    def export_failures(self, failures: List[Failure]) -> str:
        """
        Export failures to CSV string.

        Args:
            failures: List of failures

        Returns:
            CSV string representation
        """
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "test_name",
                "test_file",
                "message",
                "file",
                "line",
                "failure_type",
                "duration_ms",
            ]
        )

        # Data rows
        for failure in failures:
            location_file = failure.location.file if failure.location else ""
            location_line = failure.location.line if failure.location else ""

            writer.writerow(
                [
                    failure.test_name,
                    failure.test_file,
                    failure.message,
                    location_file,
                    location_line,
                    failure.failure_type or "",
                    failure.duration_ms if failure.duration_ms else "",
                ]
            )

        return output.getvalue()

    def export_flaky_tests(self, flaky_tests: List[FlakyTest]) -> str:
        """
        Export flaky tests to CSV string.

        Args:
            flaky_tests: List of flaky tests

        Returns:
            CSV string representation
        """
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["test_name", "pass_rate", "fail_rate", "total_runs"])

        # Data rows
        for flaky in flaky_tests:
            writer.writerow(
                [
                    flaky.test_name,
                    flaky.pass_rate,
                    flaky.fail_rate,
                    flaky.total_runs,
                ]
            )

        return output.getvalue()

    def save_to_file(self, failures: List[Failure], output_file: Path) -> None:
        """
        Save failures to CSV file.

        Args:
            failures: List of failures
            output_file: Output file path
        """
        csv_str = self.export_failures(failures)

        with open(output_file, "w", encoding="utf-8", newline="") as f:
            f.write(csv_str)
