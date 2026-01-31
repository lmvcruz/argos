"""
isort validator implementation.

This module provides the isort validator that wraps the isort parser
to provide a standard Validator interface.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from anvil.models.validator import ValidationResult, Validator
from anvil.parsers.isort_parser import IsortParser


class IsortValidator(Validator):
    """
    Validator for isort Python import sorter.

    isort is a Python utility that sorts imports alphabetically and automatically
    separates them into sections. This validator checks if imports are properly sorted.
    """

    @property
    def name(self) -> str:
        """
        Return the validator name.

        Returns:
            Validator name "isort"
        """
        return "isort"

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
            Description of what isort checks
        """
        return "Python import sorter (checks import statement order)"

    def validate(self, files: List[str], config: Dict[str, Any]) -> ValidationResult:
        """
        Run isort validation on specified files.

        Args:
            files: List of Python file paths to validate
            config: Configuration dictionary for isort

        Returns:
            ValidationResult containing validation outcome and issues
        """
        if not files:
            return ValidationResult(
                validator_name=self.name(),
                passed=True,
                errors=[],
                warnings=[],
                files_checked=0,
            )

        # Convert string paths to Path objects
        file_paths = [Path(f) for f in files]

        # Use the parser to run and parse results
        return IsortParser.run_and_parse(file_paths, config)

    def is_available(self) -> bool:
        """
        Check if isort is installed and available.

        Returns:
            True if isort is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["python", "-m", "isort", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False
