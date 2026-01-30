"""
Statistics persistence layer for saving validation results to database.

This module provides the persistence layer that saves validation results
to the statistics database after each validation run. It handles conversion
from ValidationResult objects to database records.
"""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from anvil.models.validator import ValidationResult
from anvil.storage.statistics_database import (
    FileValidationRecord,
    StatisticsDatabase,
    TestCaseRecord,
    ValidationRun,
    ValidatorRunRecord,
)


class StatisticsPersistence:
    """
    Persistence layer for saving validation results to database.

    This class converts ValidationResult objects into database records and
    saves them to the statistics database. It handles transaction management
    and error recovery.

    Examples:
        >>> db = StatisticsDatabase("anvil_stats.db")
        >>> persistence = StatisticsPersistence(db)
        >>> results = [validation_result1, validation_result2]
        >>> run_id = persistence.save_validation_run(
        ...     results=results,
        ...     git_commit="abc123",
        ...     git_branch="main",
        ...     incremental=False,
        ...     total_duration=10.5,
        ... )
    """

    def __init__(self, database: Optional[StatisticsDatabase]):
        """
        Initialize persistence layer.

        Args:
            database: StatisticsDatabase instance, or None to disable statistics
        """
        self.database = database

    def save_validation_run(
        self,
        results: List[ValidationResult],
        git_commit: Optional[str],
        git_branch: Optional[str],
        incremental: bool,
        total_duration: float,
    ) -> Optional[int]:
        """
        Save validation run and all related records to database.

        Args:
            results: List of ValidationResult objects from all validators
            git_commit: Git commit hash (if available)
            git_branch: Git branch name (if available)
            incremental: Whether this was an incremental run
            total_duration: Total duration of the validation run in seconds

        Returns:
            Database ID of the saved validation run, or None if statistics disabled
        """
        # If database is None, statistics are disabled (no-op mode)
        if self.database is None:
            return None

        # Determine overall pass/fail status
        passed = all(result.passed for result in results)

        # Create validation run record
        validation_run = ValidationRun(
            timestamp=datetime.now(),
            git_commit=git_commit,
            git_branch=git_branch,
            incremental=incremental,
            passed=passed,
            duration_seconds=total_duration,
        )

        try:
            # Insert validation run
            run_id = self.database.insert_validation_run(validation_run)

            # Save each validator's results
            for result in results:
                self._save_validator_result(run_id, result)

            return run_id

        except Exception as e:
            # Log error but don't crash the validation
            # In production, this would use proper logging
            print(f"Warning: Failed to save statistics: {e}")
            return None

    def _save_validator_result(self, run_id: int, result: ValidationResult) -> None:
        """
        Save a single validator's result and related records.

        Args:
            run_id: Database ID of the validation run
            result: ValidationResult from a single validator
        """
        # Count errors and warnings
        error_count = len(result.errors)
        warning_count = len(result.warnings)

        # Create validator run record
        validator_record = ValidatorRunRecord(
            run_id=run_id,
            validator_name=result.validator_name,
            passed=result.passed,
            error_count=error_count,
            warning_count=warning_count,
            files_checked=result.files_checked,
            duration_seconds=result.execution_time,
        )

        self.database.insert_validator_run_record(validator_record)

        # Save file-level validation results
        self._save_file_validations(run_id, result)

        # Save test case results if present
        self._save_test_results(run_id, result)

    def _save_file_validations(self, run_id: int, result: ValidationResult) -> None:
        """
        Save file-level validation results.

        Args:
            run_id: Database ID of the validation run
            result: ValidationResult containing issues
        """
        # Group issues by file
        file_issues: Dict[str, Dict[str, int]] = defaultdict(lambda: {"errors": 0, "warnings": 0})

        # Count errors per file
        for error in result.errors:
            if error.file_path:
                file_issues[error.file_path]["errors"] += 1

        # Count warnings per file
        for warning in result.warnings:
            if warning.file_path:
                file_issues[warning.file_path]["warnings"] += 1

        # Insert file validation records
        for file_path, counts in file_issues.items():
            file_record = FileValidationRecord(
                run_id=run_id,
                validator_name=result.validator_name,
                file_path=file_path,
                error_count=counts["errors"],
                warning_count=counts["warnings"],
            )
            self.database.insert_file_validation_record(file_record)

    def _save_test_results(self, run_id: int, result: ValidationResult) -> None:
        """
        Save test case results if present in metadata.

        Args:
            run_id: Database ID of the validation run
            result: ValidationResult that may contain test case metadata
        """
        # Check if result has test case metadata
        if not hasattr(result, "metadata") or result.metadata is None:
            return

        test_cases = result.metadata.get("test_cases", [])

        # Insert each test case record
        for test_case in test_cases:
            test_record = TestCaseRecord(
                run_id=run_id,
                test_name=test_case["name"],
                test_suite=test_case.get("suite", ""),
                passed=test_case["passed"],
                skipped=test_case.get("skipped", False),
                duration_seconds=test_case.get("duration", 0.0),
                failure_message=test_case.get("failure_message"),
            )
            self.database.insert_test_case_record(test_record)
