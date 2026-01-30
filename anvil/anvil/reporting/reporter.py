"""
Base reporter classes and report summary.

This module provides the base Reporter interface and ReportSummary dataclass
that all reporters must implement/use.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, TextIO

from anvil.models.validator import ValidationResult


@dataclass
class ReportSummary:
    """
    Summary statistics for validation results.

    Aggregates metrics from multiple validation results including
    pass/fail counts, error/warning counts, and execution times.

    Args:
        total_validators: Total number of validators run
        passed_validators: Number of validators that passed
        failed_validators: Number of validators that failed
        total_errors: Total number of errors across all validators
        total_warnings: Total number of warnings across all validators
        total_files_checked: Total files checked (may include duplicates)
        overall_passed: True if all validators passed
        total_execution_time: Total time spent executing validators
        timestamp: When the validation was run
    """

    total_validators: int
    passed_validators: int
    failed_validators: int
    total_errors: int
    total_warnings: int
    total_files_checked: int
    overall_passed: bool
    total_execution_time: float
    timestamp: str

    @classmethod
    def from_results(cls, results: List[ValidationResult]) -> "ReportSummary":
        """
        Create report summary from validation results.

        Args:
            results: List of validation results to summarize

        Returns:
            ReportSummary with aggregated statistics
        """
        total_validators = len(results)
        passed_validators = sum(1 for r in results if r.passed)
        failed_validators = total_validators - passed_validators
        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)
        total_files_checked = sum(r.files_checked for r in results)
        overall_passed = all(r.passed for r in results) if results else True
        total_execution_time = sum(r.execution_time or 0.0 for r in results)
        timestamp = datetime.now().isoformat()

        return cls(
            total_validators=total_validators,
            passed_validators=passed_validators,
            failed_validators=failed_validators,
            total_errors=total_errors,
            total_warnings=total_warnings,
            total_files_checked=total_files_checked,
            overall_passed=overall_passed,
            total_execution_time=total_execution_time,
            timestamp=timestamp,
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert summary to dictionary.

        Returns:
            Dictionary representation of the summary
        """
        return {
            "total_validators": self.total_validators,
            "passed_validators": self.passed_validators,
            "failed_validators": self.failed_validators,
            "total_errors": self.total_errors,
            "total_warnings": self.total_warnings,
            "total_files_checked": self.total_files_checked,
            "overall_passed": self.overall_passed,
            "total_execution_time": self.total_execution_time,
            "timestamp": self.timestamp,
        }


class Reporter:
    """
    Base class for all reporters.

    Defines the interface that all reporters must implement for
    generating validation reports in various formats.
    """

    def generate_report(
        self, results: List[ValidationResult], output_stream: TextIO = None
    ) -> None:
        """
        Generate report from validation results.

        Args:
            results: List of validation results to report
            output_stream: Stream to write report to (defaults to stdout)

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement generate_report")
