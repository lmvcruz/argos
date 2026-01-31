"""
Vulture validator implementation.

This module provides the Vulture validator that wraps the vulture parser
to provide a standard Validator interface.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from anvil.models.validator import ValidationResult, Validator
from anvil.parsers.vulture_parser import VultureParser


class VultureValidator(Validator):
    """
    Validator for vulture Python dead code detector.

    Vulture finds unused code in Python programs, including:
    - Unused functions and methods
    - Unused classes
    - Unused variables
    - Unused properties
    - Unused imports
    Each item is reported with a confidence score (0-100%).
    """

    @property
    def name(self) -> str:
        """
        Return the validator name.

        Returns:
            Validator name "vulture"
        """
        return "vulture"

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
            Description of what vulture checks
        """
        return "Python dead code detector (finds unused functions, classes, variables)"

    def validate(self, files: List[str], config: Dict[str, Any]) -> ValidationResult:
        """
        Run vulture validation on specified files.

        Args:
            files: List of Python file paths to validate
            config: Configuration dictionary for vulture

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
        return VultureParser.run_and_parse(file_paths, config)

    def is_available(self) -> bool:
        """
        Check if vulture is installed and available.

        Returns:
            True if vulture is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["python", "-m", "vulture", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False
