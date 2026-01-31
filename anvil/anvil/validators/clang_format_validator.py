"""
Validator for clang-format.

Wraps ClangFormatParser to provide validation interface.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from anvil.models.validator import ValidationResult, Validator
from anvil.parsers.clang_format_parser import ClangFormatParser


class ClangFormatValidator(Validator):
    """
    Validator for clang-format.

    Checks C++ code formatting compliance.
    """

    @property
    def name(self) -> str:
        """
        Get the name of the validator.

        Returns:
            The validator name
        """
        return "clang-format"

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
        return "Checks C++ code formatting compliance"

    def validate(
        self,
        files: List[str],
        config: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate C++ files using clang-format.

        Args:
            files: List of file paths to validate
            config: Configuration dictionary for clang-format options

        Returns:
            ValidationResult with formatting issues
        """
        file_paths = [Path(f) for f in files]
        return ClangFormatParser.run_and_parse(file_paths, config)

    def is_available(self) -> bool:
        """
        Check if clang-format is installed and available.

        Returns:
            True if clang-format is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["clang-format", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
