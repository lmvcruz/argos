"""
Console reporter for generating colored terminal output.

This module provides the ConsoleReporter class for generating
human-readable validation reports with optional colored output
and Unicode box-drawing characters.
"""

import os
import sys
from typing import List, TextIO

from anvil.models.validator import ValidationResult
from anvil.reporting.formatters import format_duration, format_issue_location
from anvil.reporting.grouping import group_issues_by_file, group_issues_by_validator
from anvil.reporting.reporter import Reporter, ReportSummary
from anvil.utils.encoding import SafeChars


def detect_color_support() -> bool:
    """
    Detect if terminal supports colored output.

    Returns:
        True if color is supported, False otherwise
    """
    # Check NO_COLOR environment variable
    if os.environ.get("NO_COLOR"):
        return False

    # Check if stdout is a TTY
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        return True

    return False


class ConsoleReporter(Reporter):
    """
    Console reporter with colored output support.

    Generates human-readable validation reports for terminal display
    with optional ANSI color codes and Unicode box-drawing characters.

    Args:
        use_color: Enable colored output (auto-detect if None)
        use_unicode: Use Unicode box-drawing characters
        verbose: Show all issue details
        quiet: Show only errors, suppress warnings
        group_by: Group issues by "file" or "validator"
    """

    # ANSI color codes
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    def __init__(
        self,
        use_color: bool = None,
        use_unicode: bool = None,
        verbose: bool = False,
        quiet: bool = False,
        group_by: str = "file",
    ):
        """Initialize console reporter with options."""
        self.use_color = use_color if use_color is not None else detect_color_support()

        # Initialize safe characters with auto-detection if not specified
        self.chars = SafeChars(force_ascii=not use_unicode if use_unicode is not None else None)

        self.verbose = verbose
        self.quiet = quiet
        self.group_by = group_by

    def generate_report(
        self, results: List[ValidationResult], output_stream: TextIO = None
    ) -> None:
        """
        Generate console report from validation results.

        Args:
            results: List of validation results to report
            output_stream: Stream to write report to (defaults to stdout)
        """
        if output_stream is None:
            output_stream = sys.stdout

        summary = ReportSummary.from_results(results)

        # Print header
        self._print_header(output_stream)

        # Print individual validator results
        if results:
            self._print_validator_results(results, output_stream)

            # Print issues grouped by file or validator
            if self.group_by == "file":
                self._print_issues_by_file(results, output_stream)
            else:
                self._print_issues_by_validator(results, output_stream)

        # Print summary
        self._print_summary(summary, output_stream)

    def _print_header(self, stream: TextIO) -> None:
        """Print report header."""
        line = self.chars.box_h * 70
        stream.write(f"{self.chars.box_tl}{line}{self.chars.box_tr}\n")
        stream.write(f"{self.chars.box_v}{' ' * 20}VALIDATION REPORT{' ' * 32}{self.chars.box_v}\n")
        stream.write(f"{self.chars.box_bl}{line}{self.chars.box_br}\n")
        stream.write("\n")

    def _print_validator_results(self, results: List[ValidationResult], stream: TextIO) -> None:
        """Print individual validator results."""
        stream.write("Validator Results:\n")
        stream.write("-" * 72 + "\n")

        for result in results:
            status_symbol = self.chars.check if result.passed else self.chars.cross
            status_text = "PASS" if result.passed else "FAIL"

            if self.use_color:
                if result.passed:
                    status = f"{self.GREEN}{status_symbol} {status_text}{self.RESET}"
                else:
                    status = f"{self.RED}{status_symbol} {status_text}{self.RESET}"
            else:
                status = f"{status_symbol} {status_text}"

            time_str = format_duration(result.execution_time or 0.0)
            stream.write(
                f"  {status}  {result.validator_name:<15} "
                f"({result.files_checked} files, {time_str})\n"
            )

        stream.write("\n")

    def _print_issues_by_file(self, results: List[ValidationResult], stream: TextIO) -> None:
        """Print issues grouped by file."""
        grouped = group_issues_by_file(results)

        if not grouped:
            return

        stream.write("Issues by File:\n")
        stream.write("-" * 72 + "\n")

        for file_path, issues in sorted(grouped.items(), key=lambda x: str(x[0])):
            stream.write(f"\n{file_path}:\n")

            for issue in issues:
                self._print_issue(issue, stream, indent=2)

        stream.write("\n")

    def _print_issues_by_validator(self, results: List[ValidationResult], stream: TextIO) -> None:
        """Print issues grouped by validator."""
        grouped = group_issues_by_validator(results)

        if not grouped:
            return

        stream.write("Issues by Validator:\n")
        stream.write("-" * 72 + "\n")

        for validator_name, issues in sorted(grouped.items()):
            stream.write(f"\n{validator_name}:\n")

            for issue in issues:
                self._print_issue(issue, stream, indent=2)

        stream.write("\n")

    def _print_issue(self, issue, stream: TextIO, indent: int = 0) -> None:
        """Print a single issue."""
        # Skip warnings in quiet mode
        if self.quiet and issue.severity == "warning":
            return

        indent_str = " " * indent
        location = format_issue_location(issue)

        # Color code by severity
        if self.use_color:
            if issue.severity == "error":
                severity_str = f"{self.RED}error{self.RESET}"
            elif issue.severity == "warning":
                severity_str = f"{self.YELLOW}warning{self.RESET}"
            else:
                severity_str = f"{self.BLUE}info{self.RESET}"
        else:
            severity_str = issue.severity

        # Basic format
        stream.write(f"{indent_str}{location}: {severity_str}: {issue.message}\n")

        # Verbose mode: show rule name and column
        if self.verbose and issue.rule_name:
            stream.write(f"{indent_str}    [{issue.rule_name}]\n")

    def _print_summary(self, summary: ReportSummary, stream: TextIO) -> None:
        """Print summary statistics."""
        line = self.chars.box_h * 70
        stream.write(f"{self.chars.box_tl}{line}{self.chars.box_tr}\n")
        stream.write(f"{self.chars.box_v}{' ' * 28}SUMMARY{' ' * 35}{self.chars.box_v}\n")
        stream.write(f"{self.chars.box_lt}{line}{self.chars.box_rt}\n")

        # Summary statistics
        stream.write(f"Total validators: {summary.total_validators}\n")
        stream.write(
            f"  Passed: {summary.passed_validators}  " f"Failed: {summary.failed_validators}\n"
        )
        stream.write(f"Total errors: {summary.total_errors}\n")
        stream.write(f"Total warnings: {summary.total_warnings}\n")
        stream.write(f"Files checked: {summary.total_files_checked}\n")
        stream.write(f"Execution time: {format_duration(summary.total_execution_time)}\n")

        # Overall result
        stream.write(f"{self.chars.box_bl}{line}{self.chars.box_br}\n")

        if summary.overall_passed:
            status_symbol = self.chars.check
            if self.use_color:
                result_str = f"{self.GREEN}{self.BOLD}{status_symbol} ALL CHECKS PASSED{self.RESET}"
            else:
                result_str = f"{status_symbol} ALL CHECKS PASSED"
        else:
            status_symbol = self.chars.cross
            if self.use_color:
                result_str = f"{self.RED}{self.BOLD}{status_symbol} VALIDATION FAILED{self.RESET}"
            else:
                result_str = f"{status_symbol} VALIDATION FAILED"

        stream.write(f"\n{result_str}\n\n")

        # Show message for empty results
        if summary.total_validators == 0:
            stream.write("No validators were run.\n")
