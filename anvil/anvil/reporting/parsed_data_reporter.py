"""
Parsed data reporter for displaying validator output in Verdict format.

This module provides the ParsedDataReporter class for displaying
validation results in the parsed dictionary format used by Verdict,
showing the actual parsed data structure.
"""

import json
import sys
from typing import Any, Dict, List, Optional, TextIO

from anvil.models.validator import ValidationResult


class ParsedDataReporter:
    """
    Reporter for displaying parsed data in Verdict-compatible format.

    Shows validation results as dictionaries with parsed data,
    similar to what Verdict adapters return. This is useful for
    debugging and understanding what data Anvil captures.

    Args:
        indent: Number of spaces for indentation (None for compact)
    """

    def __init__(self, indent: Optional[int] = 2):
        """Initialize parsed data reporter with indentation option."""
        self.indent = indent

    def generate_report(
        self, results: List[ValidationResult], output_stream: TextIO = None
    ) -> None:
        """
        Generate parsed data report from validation results.

        Args:
            results: List of validation results to report
            output_stream: Stream to write report to (defaults to stdout)
        """
        if output_stream is None:
            output_stream = sys.stdout

        parsed_results = []
        for result in results:
            parsed_results.append(self._result_to_parsed_dict(result))

        # Output each result individually for clarity
        for parsed in parsed_results:
            json.dump(parsed, output_stream, indent=self.indent)
            output_stream.write("\n")

    def _result_to_parsed_dict(self, result: ValidationResult) -> Dict[str, Any]:
        """
        Convert validation result to parsed data dictionary.

        This format matches what Verdict adapters return.

        Args:
            result: Validation result to convert

        Returns:
            Dictionary representation in Verdict adapter format
        """
        # Count errors and warnings
        error_count = len(result.errors)
        warning_count = len(result.warnings)

        # Build error code mapping (code -> count)
        error_codes = {}
        all_issues = result.errors + result.warnings

        for issue in all_issues:
            if issue.error_code:
                error_codes[issue.error_code] = error_codes.get(issue.error_code, 0) + 1

        # Build file violations structure
        file_violations = {}
        for issue in all_issues:
            if issue.file_path not in file_violations:
                file_violations[issue.file_path] = []

            violation_dict = {
                "line": issue.line_number,
                "column": issue.column_number,
                "code": issue.error_code or "unknown",
                "message": issue.message,
                "severity": issue.severity,
            }

            # Add rule_name if present
            if issue.rule_name:
                violation_dict["rule"] = issue.rule_name

            file_violations[issue.file_path].append(violation_dict)

        # Build parsed data similar to Verdict format
        parsed = {
            "validator": result.validator_name,
            "passed": result.passed,
            "total_violations": error_count + warning_count,
            "errors": error_count,
            "warnings": warning_count,
            "files_checked": result.files_checked,
            "execution_time": result.execution_time,
        }

        # Add error codes if present
        if error_codes:
            parsed["by_code"] = error_codes

        # Add file violations if present
        if file_violations:
            parsed["file_violations"] = file_violations

        return parsed
