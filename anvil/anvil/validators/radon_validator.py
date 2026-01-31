"""
Radon validator implementation.

This module provides the Radon validator that wraps the radon parser
to provide a standard Validator interface.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from anvil.models.validator import ValidationResult, Validator
from anvil.parsers.radon_parser import RadonParser


class RadonValidator(Validator):
    """
    Validator for radon Python complexity analyzer.

    Radon is a Python tool that computes various code metrics including:
    - Cyclomatic Complexity (McCabe complexity)
    - Maintainability Index
    - Raw metrics (LOC, SLOC, comments, etc.)
    - Halstead metrics
    """

    @property
    def name(self) -> str:
        """
        Return the validator name.

        Returns:
            Validator name "radon"
        """
        return "radon"

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
            Description of what radon checks
        """
        return "Python complexity analyzer (cyclomatic complexity, maintainability index)"

    def validate(self, files: List[str], config: Dict[str, Any]) -> ValidationResult:
        """
        Run radon validation on specified files.

        Args:
            files: List of Python file paths to validate
            config: Configuration dictionary for radon

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
        return RadonParser.run_and_parse(file_paths, config)

    def is_available(self) -> bool:
        """
        Check if radon is installed and available.

        Returns:
            True if radon is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["python", "-m", "radon", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False
