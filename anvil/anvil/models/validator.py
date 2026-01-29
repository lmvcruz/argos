"""
Validator interface and data models.

This module defines the abstract Validator interface and data classes
for validation results and issues.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Issue:
    """
    Represents a single validation issue (error, warning, or info).

    Attributes:
        file_path: Path to the file containing the issue
        line_number: Line number where the issue occurs
        column_number: Optional column number where the issue starts
        message: Human-readable description of the issue
        severity: Issue severity (error, warning, or info)
        rule_name: Optional name of the violated rule
        error_code: Optional error code identifier
    """

    file_path: str
    line_number: int
    message: str
    severity: str
    column_number: Optional[int] = None
    rule_name: Optional[str] = None
    error_code: Optional[str] = None

    def __post_init__(self):
        """Validate issue data after initialization."""
        valid_severities = {"error", "warning", "info"}
        if self.severity not in valid_severities:
            raise ValueError(f"Severity must be one of {valid_severities}, got: {self.severity}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Issue to dictionary.

        Returns:
            Dictionary representation of the Issue
        """
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "message": self.message,
            "severity": self.severity,
            "rule_name": self.rule_name,
            "error_code": self.error_code,
        }


@dataclass
class ValidationResult:
    """
    Result from running a single validator.

    Attributes:
        validator_name: Name of the validator that produced this result
        passed: Whether validation passed (no errors)
        errors: List of error issues found
        warnings: List of warning issues found
        execution_time: Time taken to run validation in seconds
        files_checked: Number of files that were validated
    """

    validator_name: str
    passed: bool
    errors: List[Issue] = field(default_factory=list)
    warnings: List[Issue] = field(default_factory=list)
    execution_time: float = 0.0
    files_checked: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ValidationResult to dictionary.

        Returns:
            Dictionary representation of the ValidationResult
        """
        return {
            "validator_name": self.validator_name,
            "passed": self.passed,
            "errors": [error.to_dict() for error in self.errors],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "execution_time": self.execution_time,
            "files_checked": self.files_checked,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationResult":
        """
        Create ValidationResult from dictionary.

        Args:
            data: Dictionary containing validation result data

        Returns:
            ValidationResult instance
        """
        # Convert error and warning dicts back to Issue objects
        errors = [Issue(**error) for error in data.get("errors", [])]
        warnings = [Issue(**warning) for warning in data.get("warnings", [])]

        return cls(
            validator_name=data["validator_name"],
            passed=data["passed"],
            errors=errors,
            warnings=warnings,
            execution_time=data.get("execution_time", 0.0),
            files_checked=data.get("files_checked", 0),
        )


class Validator(ABC):
    """
    Abstract base class for all validators.

    All validator implementations must inherit from this class and
    implement all abstract methods.
    """

    @abstractmethod
    def name(self) -> str:
        """
        Return the validator name.

        Returns:
            Validator name (e.g., 'flake8', 'clang-tidy')
        """

    @abstractmethod
    def language(self) -> str:
        """
        Return the supported programming language.

        Returns:
            Language name (e.g., 'python', 'cpp')
        """

    @abstractmethod
    def validate(self, files: List[str], config: Dict[str, Any]) -> ValidationResult:
        """
        Run validation on specified files with given configuration.

        Args:
            files: List of file paths to validate
            config: Configuration dictionary for this validator

        Returns:
            ValidationResult containing validation outcome and any issues found
        """

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the validator tool is installed and available.

        Returns:
            True if validator tool is available, False otherwise
        """
