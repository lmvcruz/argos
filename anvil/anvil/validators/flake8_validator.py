"""
Flake8 validator implementation.

This module provides the Flake8 validator that wraps the flake8 parser
to provide a standard Validator interface.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from anvil.models.validator import ValidationResult, Validator
from anvil.parsers.flake8_parser import Flake8Parser


class Flake8Validator(Validator):
    """
    Validator for flake8 Python linter.

    Flake8 is a Python tool that checks code style (PEP 8), programming errors
    (via PyFlakes), and cyclomatic complexity. This validator wraps the flake8
    parser to provide a standard interface.
    """

    @property
    def name(self) -> str:
        """
        Return the validator name.

        Returns:
            Validator name "flake8"
        """
        return "flake8"

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
            Description of what flake8 checks
        """
        return "Python code style checker (PEP 8, PyFlakes, cyclomatic complexity)"

    def validate(self, files: List[str], config: Dict[str, Any]) -> ValidationResult:
        """
        Run flake8 validation on specified files.

        Args:
            files: List of Python file paths to validate
            config: Configuration dictionary for flake8

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
        return Flake8Parser.run_and_parse(file_paths, config)

    def is_available(self) -> bool:
        """
        Check if flake8 is installed and available.

        Returns:
            True if flake8 is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["python", "-m", "flake8", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False
