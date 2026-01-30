"""
Helper functions for parser testing.

This module provides reusable utilities for testing validator parsers,
including fixture loading, result assertion, and issue manipulation.
"""

from pathlib import Path
from typing import Dict, List

from anvil.models.validator import Issue, ValidationResult


class ParserTestHelpers:
    """
    Helper class for parser testing.

    Provides utilities for loading fixtures, creating test objects,
    and asserting validation results.
    """

    def __init__(self):
        """Initialize helper with fixtures directory path."""
        self.fixtures_dir = Path(__file__).parent.parent / "fixtures"

    def load_fixture(self, relative_path: str) -> str:
        """
        Load a fixture file and return its contents.

        Args:
            relative_path: Path relative to fixtures directory (e.g., "python/good_code.py")

        Returns:
            Contents of the fixture file as a string

        Raises:
            FileNotFoundError: If the fixture file does not exist
        """
        fixture_path = self.fixtures_dir / relative_path
        if not fixture_path.exists():
            raise FileNotFoundError(
                f"Fixture not found: {relative_path} (looked in {fixture_path})"
            )
        return fixture_path.read_text(encoding="utf-8")

    def get_fixture_path(self, relative_path: str) -> Path:
        """
        Get the absolute path to a fixture file.

        Args:
            relative_path: Path relative to fixtures directory

        Returns:
            Absolute Path object to the fixture file

        Raises:
            FileNotFoundError: If the fixture file does not exist
        """
        fixture_path = self.fixtures_dir / relative_path
        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture not found: {relative_path}")
        return fixture_path.absolute()

    def list_fixtures(self, directory: str = "") -> List[Path]:
        """
        List all fixtures in a directory.

        Args:
            directory: Subdirectory within fixtures (e.g., "python", "cpp/bad_code")

        Returns:
            List of Path objects for all files in the directory
        """
        target_dir = self.fixtures_dir / directory if directory else self.fixtures_dir
        if not target_dir.exists():
            return []

        fixtures = []
        for item in target_dir.rglob("*"):
            if item.is_file() and not item.name.startswith("."):
                fixtures.append(item)
        return fixtures

    def create_validation_result(
        self,
        validator_name: str,
        passed: bool,
        errors: List[Issue],
        warnings: List[Issue],
        files_checked: int,
        execution_time: float = 1.0,
    ) -> ValidationResult:
        """
        Create a ValidationResult object for testing.

        Args:
            validator_name: Name of the validator
            passed: Whether validation passed
            errors: List of error issues
            warnings: List of warning issues
            files_checked: Number of files checked
            execution_time: Execution time in seconds

        Returns:
            ValidationResult object
        """
        return ValidationResult(
            validator_name=validator_name,
            passed=passed,
            errors=errors,
            warnings=warnings,
            execution_time=execution_time,
            files_checked=files_checked,
        )

    def create_issue(
        self,
        file_path: str,
        line_number: int,
        message: str,
        severity: str,
        column_number: int = 1,
        rule_name: str = "",
        error_code: str = "",
    ) -> Issue:
        """
        Create an Issue object for testing.

        Args:
            file_path: Path to the file with the issue
            line_number: Line number
            message: Issue message
            severity: Issue severity ("error", "warning", "info")
            column_number: Column number (default: 1)
            rule_name: Rule or check name (default: "")
            error_code: Error code (default: "")

        Returns:
            Issue object
        """
        return Issue(
            file_path=file_path,
            line_number=line_number,
            column_number=column_number,
            message=message,
            severity=severity,
            rule_name=rule_name,
            error_code=error_code,
        )

    def assert_validation_result_structure(self, result: ValidationResult) -> None:
        """
        Assert that a ValidationResult has the expected structure.

        Args:
            result: ValidationResult to validate

        Raises:
            AssertionError: If structure is invalid
        """
        assert isinstance(result, ValidationResult), "Must be ValidationResult instance"
        assert isinstance(result.validator_name, str), "validator_name must be string"
        assert isinstance(result.passed, bool), "passed must be boolean"
        assert isinstance(result.errors, list), "errors must be list"
        assert isinstance(result.warnings, list), "warnings must be list"
        assert isinstance(result.execution_time, (int, float)), "execution_time must be numeric"
        assert isinstance(result.files_checked, int), "files_checked must be int"
        assert result.files_checked >= 0, "files_checked must be non-negative"

        # Validate issues
        for issue in result.errors + result.warnings:
            self.assert_issue_structure(issue)

    def assert_issue_structure(self, issue: Issue) -> None:
        """
        Assert that an Issue has the expected structure.

        Args:
            issue: Issue to validate

        Raises:
            AssertionError: If structure is invalid
        """
        assert isinstance(issue, Issue), "Must be Issue instance"
        assert isinstance(issue.file_path, str), "file_path must be string"
        assert isinstance(issue.line_number, int), "line_number must be int"
        assert issue.line_number > 0, "line_number must be positive"
        assert isinstance(issue.message, str), "message must be string"
        assert len(issue.message) > 0, "message must not be empty"
        assert issue.severity in ["error", "warning", "info"], "severity must be valid"

    def count_issues_by_severity(self, issues: List[Issue]) -> Dict[str, int]:
        """
        Count issues by severity level.

        Args:
            issues: List of issues to count

        Returns:
            Dictionary mapping severity to count
        """
        counts: Dict[str, int] = {"error": 0, "warning": 0, "info": 0}
        for issue in issues:
            if issue.severity in counts:
                counts[issue.severity] += 1
        return counts

    def filter_issues_by_file(self, issues: List[Issue], file_path: str) -> List[Issue]:
        """
        Filter issues for a specific file.

        Args:
            issues: List of issues to filter
            file_path: File path to filter by

        Returns:
            List of issues for the specified file
        """
        return [issue for issue in issues if issue.file_path == file_path]

    def filter_issues_by_severity(self, issues: List[Issue], severity: str) -> List[Issue]:
        """
        Filter issues by severity level.

        Args:
            issues: List of issues to filter
            severity: Severity level to filter by

        Returns:
            List of issues with the specified severity
        """
        return [issue for issue in issues if issue.severity == severity]
