"""
Validator for include-what-you-use (IWYU).

Wraps IWYUParser to provide validation interface.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from anvil.models.validator import ValidationResult, Validator
from anvil.parsers.iwyu_parser import IWYUParser


class IWYUValidator(Validator):
    """
    Validator for include-what-you-use.

    Checks C++ include optimization and suggests improvements.
    """

    @property
    def name(self) -> str:
        """
        Get the name of the validator.

        Returns:
            The validator name
        """
        return "iwyu"

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
        return "Checks C++ include optimization and suggests improvements"

    def validate(
        self,
        files: List[str],
        config: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate C++ files using include-what-you-use.

        Args:
            files: List of file paths to validate
            config: Configuration dictionary for IWYU options

        Returns:
            ValidationResult with include suggestions
        """
        file_paths = [Path(f) for f in files]
        return IWYUParser.run_and_parse(file_paths, config)

    def is_available(self) -> bool:
        """
        Check if include-what-you-use is installed and available.

        Returns:
            True if IWYU is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["include-what-you-use", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
