"""
Pylint parser module.

This module provides parsing functionality for pylint JSON output,
extracting static analysis issues including convention, refactor,
warning, error, and fatal messages, along with code quality scores.
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from anvil.models.validator import Issue, ValidationResult


class PylintParser:
    """
    Parser for pylint JSON output.

    Parses pylint static analysis results including:
    - Convention messages (C-series): code style and naming conventions
    - Refactor suggestions (R-series): code design and structure
    - Warnings (W-series): potential issues and bad practices
    - Errors (E-series): probable bugs and undefined variables
    - Fatal errors (F-series): syntax errors and import failures
    - Code quality scores (0-10 rating)
    """

    @staticmethod
    def parse_json(json_output: str, files: List[Path]) -> ValidationResult:
        """
        Parse pylint JSON output into ValidationResult.

        Args:
            json_output: JSON string output from pylint
            files: List of files that were validated

        Returns:
            ValidationResult containing parsed issues

        Raises:
            json.JSONDecodeError: If JSON output is invalid
        """
        data = json.loads(json_output)

        errors = []
        warnings = []

        for item in data:
            message_type = item.get("type", "")
            file_path = Path(item.get("path", ""))
            line = item.get("line", 0)
            column = item.get("column", 0)
            symbol = item.get("symbol", "")
            message = item.get("message", "")
            message_id = item.get("message-id", "")

            # Map pylint message types to severity levels
            if message_type in ("error", "fatal"):
                severity = "error"
                issue_list = errors
            else:
                # convention, refactor, warning all map to warning severity
                severity = "warning"
                issue_list = warnings

            issue = Issue(
                file_path=file_path,
                line_number=line,
                column_number=column if column > 0 else None,
                severity=severity,
                rule_name=symbol,
                message=message,
                error_code=message_id,
            )
            issue_list.append(issue)

        passed = len(errors) == 0 and len(warnings) == 0

        return ValidationResult(
            validator_name="pylint",
            passed=passed,
            errors=errors,
            warnings=warnings,
            files_checked=files,
        )

    @staticmethod
    def build_command(files: List[Path], config: Dict) -> List[str]:
        """
        Build pylint command with configuration options.

        Args:
            files: List of files to validate
            config: Configuration dictionary with options:
                - disable: List of message IDs to disable
                - enable: List of message IDs to enable
                - max_line_length: Maximum line length
                - rcfile: Path to pylint configuration file
                - score: Whether to display score (default: True)

        Returns:
            List of command arguments
        """
        command = ["pylint", "--output-format=json"]

        # Add disable options
        if "disable" in config and config["disable"]:
            disable_list = ",".join(config["disable"])
            command.append(f"--disable={disable_list}")

        # Add enable options
        if "enable" in config and config["enable"]:
            enable_list = ",".join(config["enable"])
            command.append(f"--enable={enable_list}")

        # Add max line length
        if "max_line_length" in config:
            command.append(f"--max-line-length={config['max_line_length']}")

        # Add rcfile path
        if "rcfile" in config:
            command.append(f"--rcfile={config['rcfile']}")

        # Handle score option
        if "score" in config and not config["score"]:
            command.append("--score=no")

        # Add files
        for file in files:
            command.append(str(file))

        return command

    @staticmethod
    def run_pylint(
        files: List[Path], config: Dict, timeout: int = 300
    ) -> subprocess.CompletedProcess:
        """
        Execute pylint command.

        Args:
            files: List of files to validate
            config: Configuration dictionary
            timeout: Command timeout in seconds

        Returns:
            CompletedProcess with stdout and stderr

        Raises:
            FileNotFoundError: If pylint is not installed
            TimeoutError: If command exceeds timeout
        """
        command = PylintParser.build_command(files, config)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,  # pylint returns non-zero on issues
            )
            return result
        except FileNotFoundError:
            raise FileNotFoundError("pylint not found. Install with: pip install pylint")
        except subprocess.TimeoutExpired as e:
            raise TimeoutError(f"pylint command timed out after {timeout} seconds") from e

    @staticmethod
    def run_and_parse(files: List[Path], config: Dict) -> ValidationResult:
        """
        Run pylint and parse the output.

        Args:
            files: List of files to validate
            config: Configuration dictionary

        Returns:
            ValidationResult with parsed issues
        """
        result = PylintParser.run_pylint(files, config)
        return PylintParser.parse_json(result.stdout, files)

    @staticmethod
    def get_version() -> Optional[str]:
        """
        Get pylint version.

        Returns:
            Version string (e.g., "3.0.3") or None if not found
        """
        try:
            result = subprocess.run(
                ["pylint", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            # Parse version from output like:
            # "pylint 3.0.3\nastroid 3.0.2\n..."
            # or "pylint 2.17.7\n..."
            match = re.search(r"pylint\s+([\d.]+)", result.stdout)
            if match:
                return match.group(1)

            return None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    @staticmethod
    def find_config_file(directory: Path) -> Optional[Path]:
        """
        Find pylint configuration file in directory.

        Searches for configuration files in priority order:
        1. .pylintrc
        2. pyproject.toml (with [tool.pylint] section)
        3. setup.cfg (with [pylint] section)

        Args:
            directory: Directory to search

        Returns:
            Path to config file or None if not found
        """
        # Check for .pylintrc
        pylintrc = directory / ".pylintrc"
        if pylintrc.exists():
            return pylintrc

        # Check for pyproject.toml with pylint config
        pyproject = directory / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "[tool.pylint" in content:
                return pyproject

        # Check for setup.cfg with pylint config
        setup_cfg = directory / "setup.cfg"
        if setup_cfg.exists():
            content = setup_cfg.read_text()
            if "[pylint" in content:
                return setup_cfg

        return None

    @staticmethod
    def extract_score(text_output: str) -> Optional[float]:
        """
        Extract code quality score from pylint text output.

        Args:
            text_output: Text output from pylint (non-JSON mode)

        Returns:
            Score as float (0.0-10.0) or None if not found

        Examples:
            >>> extract_score("Your code has been rated at 8.50/10")
            8.50
            >>> extract_score("Your code has been rated at 9.25/10 (previous run: 8.75/10, +0.50)")
            9.25
        """
        # Pattern: "Your code has been rated at X.XX/10"
        match = re.search(r"rated at ([\d.]+)/10", text_output)
        if match:
            return float(match.group(1))

        return None
