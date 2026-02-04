"""
Black output parser for Anvil.

This module provides functionality to execute black and parse its output
(text format) into Anvil ValidationResult objects.
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from anvil.models.validator import Issue, ValidationResult


class BlackParser:
    """Parser for black code formatter output."""

    @staticmethod
    def parse_text(text_output: str, files: List[Path]) -> ValidationResult:
        """
        Parse black text output into ValidationResult.

        Args:
            text_output: Text string output from black
            files: List of files that were checked

        Returns:
            ValidationResult with parsed issues
        """
        errors = []

        # Parse "would reformat" messages (check mode)
        # Pattern: would reformat /path/to/file.py
        reformat_pattern = re.compile(r"would reformat (.+?)$", re.MULTILINE)
        for match in reformat_pattern.finditer(text_output):
            file_path_str = match.group(1).strip()

            issue = Issue(
                file_path=file_path_str,
                line_number=1,
                column_number=None,
                severity="error",
                message="File would reformat",
                rule_name="BLACK_FORMAT",
                error_code="BLACK_FORMAT",
            )
            errors.append(issue)

        # Parse "reformatted" messages (actual formatting)
        # Pattern: reformatted /path/to/file.py
        reformatted_pattern = re.compile(r"^reformatted (.+?)$", re.MULTILINE)
        for match in reformatted_pattern.finditer(text_output):
            file_path_str = match.group(1).strip()

            issue = Issue(
                file_path=file_path_str,
                line_number=1,
                column_number=None,
                severity="error",
                message="File was reformatted by black",
                rule_name="BLACK_FORMAT",
                error_code="BLACK_FORMAT",
            )
            errors.append(issue)

        # Parse "cannot format" error messages
        # Pattern: error: cannot format file.py: Cannot parse: 1:5: def foo(
        error_pattern = re.compile(r"error: cannot format (.+?):", re.MULTILINE | re.IGNORECASE)
        for match in error_pattern.finditer(text_output):
            file_path_str = match.group(1).strip()

            # Try to extract more details about the error
            error_msg = "Cannot format file (syntax error or other issue)"
            # Look for "Cannot parse" messages
            if "Cannot parse" in text_output:
                error_msg = "Cannot format file: syntax error"

            issue = Issue(
                file_path=file_path_str,
                line_number=1,
                column_number=None,
                severity="error",
                message=error_msg,
                rule_name="BLACK_ERROR",
                error_code="BLACK_ERROR",
            )
            errors.append(issue)

        # Parse "failed to reformat" summary messages
        failed_pattern = re.compile(r"(\d+) files? failed to reformat")
        if failed_pattern.search(text_output) and not errors:
            # If we have a failure summary but no specific errors, create a generic one
            issue = Issue(
                file_path=str(files[0]) if files else ".",
                line_number=1,
                column_number=None,
                severity="error",
                message="One or more files failed to reformat",
                rule_name="BLACK_ERROR",
                error_code="BLACK_ERROR",
            )
            errors.append(issue)

        passed = len(errors) == 0

        return ValidationResult(
            validator_name="black",
            passed=passed,
            errors=errors,
            warnings=[],
            files_checked=len(files),
        )

    @staticmethod
    def extract_code_from_diff(diff_output: str) -> tuple:
        """
        Extract actual and expected code from Black diff output.

        Args:
            diff_output: Diff string from black --diff output

        Returns:
            Tuple of (actual_code, expected_code) where:
            - actual_code: Original code (lines starting with -)
            - expected_code: Fixed code (lines starting with +)
        """
        actual_lines = []
        expected_lines = []

        # Process each line in the diff
        for line in diff_output.split("\n"):
            # Skip headers and context lines
            if line.startswith("---") or line.startswith("+++"):
                # Header lines
                continue
            elif line.startswith("@@"):
                # Hunk header
                continue
            elif line.startswith("-") and not line.startswith("---"):
                # Removed line (actual code)
                actual_lines.append(line[1:])
            elif line.startswith("+") and not line.startswith("+++"):
                # Added line (expected code)
                expected_lines.append(line[1:])
            # Lines starting with space or empty are context, skip them

        actual_code = "\n".join(actual_lines)
        expected_code = "\n".join(expected_lines)

        return actual_code, expected_code

    @staticmethod
    def build_command(files: List[Path], config: Optional[Dict] = None) -> List[str]:
        """
        Build black command with configuration options.

        Args:
            files: List of files to check
            config: Configuration dictionary with options

        Returns:
            Command as list of strings
        """
        if config is None:
            config = {}

        cmd = ["python", "-m", "black", "--check"]

        # Add line length option
        if "line_length" in config:
            cmd.append(f"--line-length={config['line_length']}")

        # Add target version(s)
        if "target_version" in config:
            target_versions = config["target_version"]
            if isinstance(target_versions, list):
                for version in target_versions:
                    cmd.append(f"--target-version={version}")
            else:
                cmd.append(f"--target-version={target_versions}")

        # Add skip string normalization
        if config.get("skip_string_normalization", False):
            cmd.append("--skip-string-normalization")

        # Add diff output
        if config.get("diff", False):
            cmd.append("--diff")

        # Add color output
        if config.get("color", False):
            cmd.append("--color")

        # Add file paths
        cmd.extend([str(f) for f in files])

        return cmd

    @staticmethod
    def get_version() -> Optional[str]:
        """
        Get black version.

        Returns:
            Version string or None if black not found
        """
        try:
            result = subprocess.run(
                ["python", "-m", "black", "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            # Version output is like: "black, 24.1.0 (compiled: yes)"
            version_line = result.stdout.strip().split("\n")[0]
            # Extract version number
            match = re.search(r"(\d+\.\d+\.\d+)", version_line)
            if match:
                return match.group(1)
            # Fallback: extract first number sequence
            parts = version_line.split()
            for part in parts:
                if re.match(r"\d+\.\d+", part):
                    return part.rstrip(",")
            return None
        except (FileNotFoundError, subprocess.SubprocessError, IndexError):
            return None

    @staticmethod
    def run_black(
        files: List[Path], config: Optional[Dict] = None, timeout: Optional[int] = None
    ) -> str:
        """
        Execute black and return output.

        Args:
            files: List of files to check
            config: Configuration dictionary
            timeout: Command timeout in seconds

        Returns:
            Black output as string

        Raises:
            FileNotFoundError: If black is not installed
            subprocess.TimeoutExpired: If command times out
        """
        cmd = BlackParser.build_command(files, config)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or (config.get("timeout") if config else None),
            )

            # Black returns:
            # - 0 if nothing would change
            # - 1 if files would be reformatted
            # - 123 if there's a syntax error
            # We capture both stdout and stderr
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            output = stdout + "\n" + stderr
            return output.strip()

        except FileNotFoundError:
            raise FileNotFoundError("black not found. Please install it: pip install black")
        except subprocess.TimeoutExpired as e:
            raise TimeoutError(f"black command timed out after {timeout} seconds") from e

    @staticmethod
    def run_and_parse(files: List[Path], config: Optional[Dict] = None) -> ValidationResult:
        """
        Run black and parse results.

        Args:
            files: List of files to check
            config: Configuration dictionary

        Returns:
            ValidationResult with parsed issues
        """
        try:
            output = BlackParser.run_black(files, config)

            # Parse text output
            return BlackParser.parse_text(output, files)

        except (FileNotFoundError, TimeoutError) as e:
            # Return failed result with error
            return ValidationResult(
                validator_name="black",
                passed=False,
                errors=[
                    Issue(
                        file_path=str(files[0]) if files else ".",
                        line_number=1,
                        column_number=None,
                        severity="error",
                        message=str(e),
                        rule_name="BLACK_ERROR",
                        error_code="BLACK_ERROR",
                    )
                ],
                warnings=[],
                files_checked=len(files),
            )

    @staticmethod
    def find_config_file(directory: Path) -> Optional[Path]:
        """
        Find black configuration file in directory.

        Checks for:
        1. pyproject.toml (with [tool.black] section)

        Args:
            directory: Directory to search

        Returns:
            Path to config file or None if not found
        """
        # Check for pyproject.toml
        pyproject = directory / "pyproject.toml"
        if pyproject.exists():
            # Check if it has [tool.black] section
            content = pyproject.read_text()
            if "[tool.black]" in content:
                return pyproject

        return None

    @staticmethod
    def generate_fix_command(files: List[Path], config: Optional[Dict] = None) -> str:
        """
        Generate command to fix formatting issues.

        Args:
            files: List of files to format
            config: Configuration dictionary

        Returns:
            Command string to fix issues
        """
        if config is None:
            config = {}

        cmd_parts = ["python", "-m", "black"]

        # Add configuration options (same as build_command but without --check)
        if "line_length" in config:
            cmd_parts.append(f"--line-length={config['line_length']}")

        if "target_version" in config:
            target_versions = config["target_version"]
            if isinstance(target_versions, list):
                for version in target_versions:
                    cmd_parts.append(f"--target-version={version}")
            else:
                cmd_parts.append(f"--target-version={target_versions}")

        if config.get("skip_string_normalization", False):
            cmd_parts.append("--skip-string-normalization")

        # Add file paths
        cmd_parts.extend([str(f) for f in files])

        return " ".join(cmd_parts)
