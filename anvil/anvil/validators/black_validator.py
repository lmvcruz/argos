"""
Black validator implementation.

This module provides the Black validator that wraps the black parser
to provide a standard Validator interface.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from anvil.models.validator import ValidationResult, Validator
from anvil.parsers.black_parser import BlackParser

# Set up logger for anvil.black
logger = logging.getLogger('anvil.black')


class BlackValidator(Validator):
    """
    Validator for black Python code formatter.

    Black is an opinionated Python code formatter that enforces a consistent
    style. This validator checks if code matches black's formatting rules.
    """

    @property
    def name(self) -> str:
        """
        Return the validator name.

        Returns:
            Validator name "black"
        """
        return "black"

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
            Description of what black checks
        """
        return "Python code formatter (checks formatting compliance)"

    def validate(self, files: List[str], config: Dict[str, Any]) -> ValidationResult:
        """
        Run black validation on specified files.

        Args:
            files: List of Python file paths to validate
            config: Configuration dictionary for black

        Returns:
            ValidationResult containing validation outcome and issues
        """
        if not files:
            logger.info("Black validator called with no files")
            return ValidationResult(
                validator_name=self.name(),
                passed=True,
                errors=[],
                warnings=[],
                files_checked=0,
            )

        logger.info(f"Black validator: checking {len(files)} files")
        logger.debug(f"Black validator: files={files}, config={config}")

        # Convert string paths to Path objects
        file_paths = [Path(f) for f in files]

        # Use the parser to run and parse results
        result = BlackParser.run_and_parse(file_paths, config)

        logger.info(
            f"Black validation complete: {len(result.errors)} errors, "
            f"{len(result.warnings)} warnings, {result.files_checked} files checked"
        )
        logger.debug(f"Black validation result: {result}")

        return result

    def is_available(self) -> bool:
        """
        Check if black is installed and available.

        Returns:
            True if black is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["python", "-m", "black", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False
