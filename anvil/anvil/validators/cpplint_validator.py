"""
Validator for cpplint.

Wraps CpplintParser to provide validation interface.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from anvil.models.validator import ValidationResult, Validator
from anvil.parsers.cpplint_parser import CpplintParser


class CpplintValidator(Validator):
    """
    Validator for cpplint style checking.

    Checks C++ code for Google C++ Style Guide violations.
    """

    @property
    def name(self) -> str:
        """
        Get the name of the validator.

        Returns:
            The validator name
        """
        return "cpplint"

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
        return "Checks C++ code for Google C++ Style Guide violations"

    def validate(
        self,
        files: List[str],
        config: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate C++ files using cpplint.

        Args:
            files: List of file paths to validate
            config: Configuration dictionary for cpplint options

        Returns:
            ValidationResult with errors and warnings
        """
        file_paths = [Path(f) for f in files]
        return CpplintParser.run_and_parse(file_paths, config)

    def is_available(self) -> bool:
        """
        Check if cpplint is installed and available.

        Returns:
            True if cpplint is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["cpplint", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
