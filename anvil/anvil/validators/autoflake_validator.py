"""
autoflake validator implementation.

This module provides the autoflake validator that wraps the autoflake parser
to provide a standard Validator interface.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from anvil.models.validator import ValidationResult, Validator
from anvil.parsers.autoflake_parser import AutoflakeParser


class AutoflakeValidator(Validator):
    """
    Validator for autoflake Python unused code remover.

    autoflake removes unused imports and unused variables from Python code.
    This validator checks for unused code that should be removed.
    """

    @property
    def name(self) -> str:
        """
        Return the validator name.

        Returns:
            Validator name "autoflake"
        """
        return "autoflake"

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
            Description of what autoflake checks
        """
        return "Python unused code detector (finds unused imports and variables)"

    def validate(self, files: List[str], config: Dict[str, Any]) -> ValidationResult:
        """
        Run autoflake validation on specified files.

        Args:
            files: List of Python file paths to validate
            config: Configuration dictionary for autoflake

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
        return AutoflakeParser.run_and_parse(file_paths, config)

    def is_available(self) -> bool:
        """
        Check if autoflake is installed and available.

        Returns:
            True if autoflake is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["python", "-m", "autoflake", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False
