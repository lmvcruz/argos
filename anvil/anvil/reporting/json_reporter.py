"""
JSON reporter for generating machine-readable output.

This module provides the JSONReporter class for generating
validation reports in JSON format for programmatic consumption.
"""

import json
import sys
from typing import Any, Dict, List, Optional, TextIO

from anvil.models.validator import ValidationResult
from anvil.reporting.reporter import Reporter, ReportSummary


class JSONReporter(Reporter):
    """
    JSON reporter for machine-readable output.

    Generates validation reports in JSON format suitable for
    programmatic consumption by CI/CD systems or other tools.

    Args:
        indent: Number of spaces for indentation (None for compact)
    """

    def __init__(self, indent: Optional[int] = 2):
        """Initialize JSON reporter with indentation option."""
        self.indent = indent

    def generate_report(
        self, results: List[ValidationResult], output_stream: TextIO = None
    ) -> None:
        """
        Generate JSON report from validation results.

        Args:
            results: List of validation results to report
            output_stream: Stream to write report to (defaults to stdout)
        """
        if output_stream is None:
            output_stream = sys.stdout

        summary = ReportSummary.from_results(results)

        report_data = {
            "summary": summary.to_dict(),
            "results": [self._result_to_dict(r) for r in results],
            "timestamp": summary.timestamp,
        }

        json.dump(report_data, output_stream, indent=self.indent)
        output_stream.write("\n")

    def _result_to_dict(self, result: ValidationResult) -> Dict[str, Any]:
        """
        Convert validation result to dictionary.

        Args:
            result: Validation result to convert

        Returns:
            Dictionary representation of the result
        """
        return {
            "validator_name": result.validator_name,
            "passed": result.passed,
            "errors": [self._issue_to_dict(e) for e in result.errors],
            "warnings": [self._issue_to_dict(w) for w in result.warnings],
            "files_checked": result.files_checked,
            "execution_time": result.execution_time,
        }

    def _issue_to_dict(self, issue) -> Dict[str, Any]:
        """
        Convert issue to dictionary.

        Args:
            issue: Issue to convert

        Returns:
            Dictionary representation of the issue
        """
        return {
            "file_path": issue.file_path,
            "line_number": issue.line_number,
            "column_number": issue.column_number,
            "message": issue.message,
            "severity": issue.severity,
            "rule_name": issue.rule_name,
            "error_code": issue.error_code,
        }
