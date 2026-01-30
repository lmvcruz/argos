"""
Flake8 output parser for Anvil.

This module provides functionality to execute flake8 and parse its output
(JSON or text format) into Anvil ValidationResult objects.
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from anvil.models.validator import Issue, ValidationResult


class Flake8Parser:
    """Parser for flake8 linting tool output."""

    @staticmethod
    def map_severity(code: str) -> str:
        """
        Map flake8 error code to Anvil severity level.

        Args:
            code: Flake8 error code (e.g., "E501", "W503", "F401")

        Returns:
            Severity level: "error", "warning", or "info"
        """
        if not code:
            return "error"

        # First character determines the category
        prefix = code[0].upper()

        # E-series: PEP 8 errors - critical
        # F-series: PyFlakes errors - critical (undefined names, imports, etc.)
        if prefix in ["E", "F"]:
            return "error"

        # W-series: PEP 8 warnings - less critical style issues
        # C-series: Complexity warnings - code quality
        # N-series: Naming conventions - style
        # D-series: Docstring issues - documentation
        if prefix in ["W", "C", "N", "D"]:
            return "warning"

        # Default to info for unknown categories
        return "info"

    @staticmethod
    def parse_json(json_output: str, files: List[Path]) -> ValidationResult:
        """
        Parse flake8 JSON output into ValidationResult.

        Args:
            json_output: JSON string output from flake8
            files: List of files that were checked

        Returns:
            ValidationResult with parsed issues

        Raises:
            json.JSONDecodeError: If output is not valid JSON
        """
        data = json.loads(json_output)

        errors = []
        warnings = []

        # Flake8 JSON format: {filename: [issues]}
        for filename, issues in data.items():
            file_path = Path(filename)

            for issue in issues:
                code = issue.get("code", "")
                severity = Flake8Parser.map_severity(code)

                anvil_issue = Issue(
                    file_path=file_path,
                    line_number=issue.get("line_number", 1),
                    column_number=issue.get("column_number"),
                    severity=severity,
                    message=issue.get("text", ""),
                    rule_name=code,
                    error_code=code,
                )

                if severity == "error":
                    errors.append(anvil_issue)
                else:
                    warnings.append(anvil_issue)

        passed = len(errors) == 0 and len(warnings) == 0

        return ValidationResult(
            validator_name="flake8",
            passed=passed,
            errors=errors,
            warnings=warnings,
            files_checked=len(files),
        )

    @staticmethod
    def parse_text(text_output: str, files: List[Path]) -> ValidationResult:
        """
        Parse flake8 text output into ValidationResult.

        Fallback parser for text format:
        filename:line:column: CODE message

        Args:
            text_output: Text output from flake8
            files: List of files that were checked

        Returns:
            ValidationResult with parsed issues
        """
        errors = []
        warnings = []

        if not text_output.strip():
            return ValidationResult(
                validator_name="flake8",
                passed=True,
                errors=[],
                warnings=[],
                files_checked=len(files),
            )

        for line in text_output.strip().split("\n"):
            if not line.strip():
                continue

            # Parse format: filename:line:column: CODE message
            # Use regex to handle both Unix and Windows paths properly
            # Pattern: (filepath):(line):(column): (CODE) (message)
            match = re.match(r"^(.+?):(\d+):(\d+):\s+(\S+)\s+(.+)$", line)
            if not match:
                continue

            try:
                filename = match.group(1)
                line_num = int(match.group(2))
                col_num = int(match.group(3))
                code = match.group(4)
                message = match.group(5)

                severity = Flake8Parser.map_severity(code)

                issue = Issue(
                    file_path=Path(filename),
                    line_number=line_num,
                    column_number=col_num,
                    severity=severity,
                    message=message,
                    rule_name=code,
                    error_code=code,
                )

                if severity == "error":
                    errors.append(issue)
                else:
                    warnings.append(issue)

            except (ValueError, IndexError):
                # Skip malformed lines
                continue

        passed = len(errors) == 0 and len(warnings) == 0

        return ValidationResult(
            validator_name="flake8",
            passed=passed,
            errors=errors,
            warnings=warnings,
            files_checked=len(files),
        )

    @staticmethod
    def build_command(files: List[Path], config: Optional[Dict] = None) -> List[str]:
        """
        Build flake8 command with configuration options.

        Args:
            files: List of files to check
            config: Configuration dictionary with options

        Returns:
            Command as list of strings
        """
        if config is None:
            config = {}

        cmd = ["python", "-m", "flake8"]

        # Add ignore patterns
        if "ignore" in config and config["ignore"]:
            ignore_list = ",".join(config["ignore"])
            cmd.append(f"--ignore={ignore_list}")

        # Add select patterns
        if "select" in config and config["select"]:
            select_list = ",".join(config["select"])
            cmd.append(f"--select={select_list}")

        # Add max line length
        if "max_line_length" in config:
            cmd.append(f"--max-line-length={config['max_line_length']}")

        # Add exclude patterns
        if "exclude" in config and config["exclude"]:
            exclude_list = ",".join(config["exclude"])
            cmd.append(f"--exclude={exclude_list}")

        # Add max complexity
        if "max_complexity" in config:
            cmd.append(f"--max-complexity={config['max_complexity']}")

        # Add file paths
        cmd.extend([str(f) for f in files])

        return cmd

    @staticmethod
    def get_version() -> Optional[str]:
        """
        Get flake8 version.

        Returns:
            Version string or None if flake8 not found
        """
        try:
            result = subprocess.run(
                ["python", "-m", "flake8", "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            # Version output is like: "7.0.0 ..."
            version_line = result.stdout.strip().split("\n")[0]
            version = version_line.split()[0]
            return version
        except (FileNotFoundError, subprocess.SubprocessError, IndexError):
            return None

    @staticmethod
    def run_flake8(
        files: List[Path], config: Optional[Dict] = None, timeout: Optional[int] = None
    ) -> str:
        """
        Execute flake8 and return output.

        Args:
            files: List of files to check
            config: Configuration dictionary
            timeout: Command timeout in seconds

        Returns:
            Flake8 output as string

        Raises:
            FileNotFoundError: If flake8 is not installed
            subprocess.TimeoutExpired: If command times out
        """
        cmd = Flake8Parser.build_command(files, config)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or config.get("timeout") if config else None,
            )
            # Flake8 returns non-zero when issues are found, which is expected
            return result.stdout

        except FileNotFoundError:
            raise FileNotFoundError("flake8 not found. Please install it: pip install flake8")
        except subprocess.TimeoutExpired as e:
            raise TimeoutError(f"flake8 command timed out after {timeout} seconds") from e

    @staticmethod
    def run_and_parse(files: List[Path], config: Optional[Dict] = None) -> ValidationResult:
        """
        Run flake8 and parse results.

        Args:
            files: List of files to check
            config: Configuration dictionary

        Returns:
            ValidationResult with parsed issues
        """
        try:
            output = Flake8Parser.run_flake8(files, config)

            # Use text parsing (default format)
            return Flake8Parser.parse_text(output, files)

        except (FileNotFoundError, TimeoutError) as e:
            # Return failed result with error
            return ValidationResult(
                validator_name="flake8",
                passed=False,
                errors=[
                    Issue(
                        file_path=files[0] if files else Path("."),
                        line_number=1,
                        column_number=None,
                        severity="error",
                        message=str(e),
                        rule_name="FLAKE8_ERROR",
                        error_code="FLAKE8_ERROR",
                    )
                ],
                warnings=[],
                files_checked=len(files),
            )

    @staticmethod
    def find_config_file(directory: Path) -> Optional[Path]:
        """
        Find flake8 configuration file in directory.

        Checks for (in order):
        1. .flake8
        2. setup.cfg (with [flake8] section)
        3. tox.ini (with [flake8] section)

        Args:
            directory: Directory to search

        Returns:
            Path to config file or None if not found
        """
        # Check for .flake8
        flake8_file = directory / ".flake8"
        if flake8_file.exists():
            return flake8_file

        # Check for setup.cfg with [flake8] section
        setup_cfg = directory / "setup.cfg"
        if setup_cfg.exists():
            content = setup_cfg.read_text()
            if "[flake8]" in content:
                return setup_cfg

        # Check for tox.ini with [flake8] section
        tox_ini = directory / "tox.ini"
        if tox_ini.exists():
            content = tox_ini.read_text()
            if "[flake8]" in content:
                return tox_ini

        return None
