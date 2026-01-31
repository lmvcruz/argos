"""
Validator for clang-tidy.

Wraps ClangTidyParser to provide validation interface.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from anvil.models.validator import ValidationResult, Validator
from anvil.parsers.clang_tidy_parser import ClangTidyParser


class ClangTidyValidator(Validator):
    """
    Validator for clang-tidy static analysis.

    Checks C++ code for bugs, performance issues, and style violations.
    """

    @property
    def name(self) -> str:
        """
        Get the name of the validator.

        Returns:
            The validator name
        """
        return "clang-tidy"

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
        return "Checks C++ code for bugs, performance issues, and style violations"

    def validate(
        self,
        files: List[str],
        config: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate C++ files using clang-tidy.

        Args:
            files: List of file paths to validate
            config: Configuration dictionary for clang-tidy options

        Returns:
            ValidationResult with errors and warnings
        """
        file_paths = [Path(f) for f in files]
        return ClangTidyParser.run_and_parse(file_paths, config)

    def is_available(self) -> bool:
        """
        Check if clang-tidy is installed and available.

        Returns:
            True if clang-tidy is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["clang-tidy", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
