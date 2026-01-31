"""
Pytest validator implementation.

This module provides the Pytest validator that wraps the pytest parser
to provide a standard Validator interface.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from anvil.models.validator import ValidationResult, Validator
from anvil.parsers.pytest_parser import PytestParser


class PytestValidator(Validator):
    """
    Validator for pytest Python testing framework.

    Pytest is a comprehensive Python testing framework that supports:
    - Unit testing with detailed assertions
    - Test discovery and parametrization
    - Fixture management
    - Coverage measurement (with pytest-cov plugin)
    - Parallel test execution
    This validator runs tests and reports failures, coverage, and performance.
    """

    @property
    def name(self) -> str:
        """
        Return the validator name.

        Returns:
            Validator name "pytest"
        """
        return "pytest"

    @property
    def language(self) -> str:
        """
        Return the supported programming language.

        Returns:
            Language name "python"
        """
        return "python"

    @property
    def description(self) -> str:
        """
        Return validator description.

        Returns:
            Description of what pytest checks
        """
        return "Python testing framework (runs tests, measures coverage, reports failures)"

    def validate(self, files: List[str], config: Dict[str, Any]) -> ValidationResult:
        """
        Run pytest validation on specified files.

        Args:
            files: List of Python test file paths to validate
            config: Configuration dictionary for pytest

        Returns:
            ValidationResult containing validation outcome and issues
        """
        if not files:
            return ValidationResult(
                validator_name=self.name,
                passed=True,
                errors=[],
                warnings=[],
                files_checked=0,
            )

        # Convert string paths to Path objects
        file_paths = [Path(f) for f in files]

        # Use the parser to run and parse results
        return PytestParser.run_and_parse(file_paths, config)

    def is_available(self) -> bool:
        """
        Check if pytest is installed and available.

        Returns:
            True if pytest is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False
