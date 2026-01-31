"""
Validator for cppcheck.

Wraps CppcheckParser to provide validation interface.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from anvil.models.validator import ValidationResult, Validator
from anvil.parsers.cppcheck_parser import CppcheckParser


class CppcheckValidator(Validator):
    """
    Validator for cppcheck static analysis.

    Checks C++ code for bugs, undefined behavior, and memory issues.
    """

    @property
    def name(self) -> str:
        """
        Get the name of the validator.

        Returns:
            The validator name
        """
        return "cppcheck"

    @property
    def language(self) -> str:
        """
        Get the language supported by this validator.

        Returns:
            The language identifier
        """
        return "cpp"

    @property
    def description(self) -> str:
        """
        Get a description of what this validator checks.

        Returns:
            A brief description of the validator's purpose
        """
        return "Checks C++ code for bugs, undefined behavior, and memory issues"

    def validate(
        self,
        files: List[str],
        config: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate C++ files using cppcheck.

        Args:
            files: List of file paths to validate
            config: Configuration dictionary for cppcheck options

        Returns:
            ValidationResult with errors and warnings
        """
        file_paths = [Path(f) for f in files]
        return CppcheckParser.run_and_parse(file_paths, config)

    def is_available(self) -> bool:
        """
        Check if cppcheck is installed and available.

        Returns:
            True if cppcheck is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["cppcheck", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
