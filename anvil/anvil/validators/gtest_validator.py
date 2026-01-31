"""
Validator for Google Test (gtest).

Wraps GTestParser to provide validation interface.
"""

from pathlib import Path
from typing import Any, Dict, List

from anvil.models.validator import ValidationResult, Validator
from anvil.parsers.gtest_parser import GTestParser


class GTestValidator(Validator):
    """
    Validator for Google Test.

    Runs C++ tests and reports results.
    """

    @property
    def name(self) -> str:
        """
        Get the name of the validator.

        Returns:
            The validator name
        """
        return "gtest"

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
        return "Runs C++ tests and reports results"

    def validate(
        self,
        files: List[str],
        config: Dict[str, Any],
    ) -> ValidationResult:
        """
        Validate C++ files by running Google Test tests.

        Args:
            files: List of test binary paths to execute
            config: Configuration dictionary for gtest options

        Returns:
            ValidationResult with test results
        """
        file_paths = [Path(f) for f in files]
        return GTestParser.run_and_parse(file_paths, config)

    def is_available(self) -> bool:
        """
        Check if Google Test test binaries are available.

        Returns:
            True if gtest binary is configured, False otherwise
        """
        # GTest is not a standalone tool, it's a testing framework
        # Availability depends on having test binaries built
        # Return True here since parsers will handle missing binaries
        return True
