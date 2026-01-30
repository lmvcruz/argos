"""
Parser for autoflake output.

This module provides parsing functionality for autoflake text output to detect
unused imports, unused variables, and duplicate keys in Python code.
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from anvil.models.validator import Issue, ValidationResult


class AutoflakeParser:
    """
    Parser for autoflake output.

    Autoflake removes unused imports and unused variables from Python code.
    This parser processes the unified diff output to identify files with issues.
    """

    @staticmethod
    def parse_text(text_output: str, files: List[Path]) -> ValidationResult:
        """
        Parse autoflake text output into ValidationResult.

        Autoflake outputs a unified diff format showing what would be removed.
        Each file with issues starts with "--- filename (original)".

        Args:
            text_output: Raw text output from autoflake
            files: List of files that were checked

        Returns:
            ValidationResult with errors for files needing cleanup
        """
        errors = []
        warnings = []

        if not text_output or text_output.strip() == "":
            # Empty output means no issues found
            return ValidationResult(
                validator_name="autoflake",
                passed=True,
                errors=errors,
                warnings=warnings,
            )

        # Parse diff format to extract files with issues
        # Pattern: --- filename (original)
        file_pattern = re.compile(r"^---\s+(.+?)\s+\(original\)", re.MULTILINE)
        matches = file_pattern.findall(text_output)

        for file_match in matches:
            # Normalize path for comparison
            file_path = Path(file_match).as_posix()

            # Create error for this file
            error = Issue(
                file_path=file_path,
                line_number=1,
                column_number=None,
                severity="error",
                message=(
                    "File contains unused imports, unused variables, "
                    "or duplicate keys that can be removed"
                ),
                rule_name="unused-code",
            )
            errors.append(error)

        passed = len(errors) == 0
        return ValidationResult(
            validator_name="autoflake",
            passed=passed,
            errors=errors,
            warnings=warnings,
        )

    @staticmethod
    def build_command(files: List[Path], config: Optional[Dict] = None) -> List[str]:
        """
        Build autoflake command with configuration options.

        Args:
            files: List of files to check
            config: Configuration dictionary with options

        Returns:
            Command as list of strings
        """
        if config is None:
            config = {}

        command = ["autoflake", "--check"]

        # Add configuration options
        if config.get("remove_unused_variables"):
            command.append("--remove-unused-variables")

        if config.get("remove_all_unused_imports"):
            command.append("--remove-all-unused-imports")

        if config.get("ignore_init_module_imports"):
            command.append("--ignore-init-module-imports")

        if config.get("expand_star_imports"):
            command.append("--expand-star-imports")

        if config.get("remove_duplicate_keys"):
            command.append("--remove-duplicate-keys")

        # Handle imports to ignore
        imports_to_ignore = config.get("imports", [])
        if imports_to_ignore:
            imports_str = ",".join(imports_to_ignore)
            command.append(f"--imports={imports_str}")

        # Add files
        for file_path in files:
            command.append(str(file_path))

        return command

    @staticmethod
    def run_autoflake(
        files: List[Path],
        config: Optional[Dict] = None,
        timeout: int = 60,
    ) -> str:
        """
        Execute autoflake and return output.

        Args:
            files: List of files to check
            config: Configuration dictionary
            timeout: Timeout in seconds

        Returns:
            Combined stdout and stderr from autoflake

        Raises:
            FileNotFoundError: If autoflake is not installed
            TimeoutError: If autoflake execution times out
        """
        command = AutoflakeParser.build_command(files, config)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )

            # Combine stdout and stderr
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr

            return output if output else ""

        except subprocess.TimeoutExpired as e:
            raise TimeoutError(f"autoflake execution timed out after {timeout} seconds") from e
        except FileNotFoundError as e:
            raise FileNotFoundError(
                "autoflake not found. Install with: pip install autoflake"
            ) from e

    @staticmethod
    def run_and_parse(files: List[Path], config: Optional[Dict] = None) -> ValidationResult:
        """
        Run autoflake and parse the output.

        High-level method that combines execution and parsing.

        Args:
            files: List of files to check
            config: Configuration dictionary

        Returns:
            ValidationResult with parsed results
        """
        output = AutoflakeParser.run_autoflake(files, config)
        return AutoflakeParser.parse_text(output, files)

    @staticmethod
    def get_version() -> Optional[str]:
        """
        Detect autoflake version.

        Returns:
            Version string (e.g., "2.2.1") or None if not installed
        """
        try:
            result = subprocess.run(
                ["autoflake", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            # Parse version from output like "autoflake 2.2.1"
            version_pattern = re.compile(r"autoflake\s+([\d.]+)")
            match = version_pattern.search(result.stdout)

            if match:
                return match.group(1)

            return None

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    @staticmethod
    def find_config_file(directory: Path) -> Optional[Path]:
        """
        Find autoflake configuration file.

        Searches for configuration in pyproject.toml or setup.cfg.

        Args:
            directory: Directory to search from

        Returns:
            Path to config file or None if not found
        """
        # Check for pyproject.toml with [tool.autoflake] section
        pyproject = directory / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "[tool.autoflake]" in content:
                return pyproject

        # Check for setup.cfg with [autoflake] section
        setup_cfg = directory / "setup.cfg"
        if setup_cfg.exists():
            content = setup_cfg.read_text()
            if "[autoflake]" in content:
                return setup_cfg

        return None

    @staticmethod
    def generate_fix_command(files: List[Path], config: Optional[Dict] = None) -> List[str]:
        """
        Generate command to automatically fix issues.

        Creates the same command as build_command but with --in-place
        instead of --check.

        Args:
            files: List of files to fix
            config: Configuration dictionary

        Returns:
            Command as list of strings for fixing issues
        """
        if config is None:
            config = {}

        command = ["autoflake", "--in-place"]

        # Add configuration options (same as build_command)
        if config.get("remove_unused_variables"):
            command.append("--remove-unused-variables")

        if config.get("remove_all_unused_imports"):
            command.append("--remove-all-unused-imports")

        if config.get("ignore_init_module_imports"):
            command.append("--ignore-init-module-imports")

        if config.get("expand_star_imports"):
            command.append("--expand-star-imports")

        if config.get("remove_duplicate_keys"):
            command.append("--remove-duplicate-keys")

        # Handle imports to ignore
        imports_to_ignore = config.get("imports", [])
        if imports_to_ignore:
            imports_str = ",".join(imports_to_ignore)
            command.append(f"--imports={imports_str}")

        # Add files
        for file_path in files:
            command.append(str(file_path))

        return command
