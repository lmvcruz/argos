"""
Pylint validator implementation.

This module provides the Pylint validator that wraps the pylint parser
to provide a standard Validator interface.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from anvil.models.validator import ValidationResult, Validator
from anvil.parsers.pylint_parser import PylintParser


class PylintValidator(Validator):
    """
    Validator for pylint Python static analyzer.

    Pylint is a comprehensive Python static analysis tool that checks for errors,
    enforces coding standards, looks for code smells, and provides refactoring suggestions.
    It also computes code quality scores.
    """

    @property
    def name(self) -> str:
        """
        Return the validator name.

        Returns:
            Validator name "pylint"
        """
        return "pylint"

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
            Description of what pylint checks
        """
        return "Python static analyzer (comprehensive error checking, code quality scoring)"

    def validate(self, files: List[str], config: Dict[str, Any]) -> ValidationResult:
        """
        Run pylint validation on specified files.

        Args:
            files: List of Python file paths to validate
            config: Configuration dictionary for pylint

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
        return PylintParser.run_and_parse(file_paths, config)

    def is_available(self) -> bool:
        """
        Check if pylint is installed and available.

        Returns:
            True if pylint is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["python", "-m", "pylint", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False
