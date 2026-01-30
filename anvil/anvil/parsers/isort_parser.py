"""
Parser for isort output (Step 2.4).

This module provides functionality to parse isort text output into
Anvil's ValidationResult format. It executes isort in check mode and
detects files with incorrectly sorted/formatted imports.

isort exit codes:
- 0: All imports are correctly sorted
- 1: Files were found that need to be sorted

Key features:
- Parse isort ERROR messages for incorrectly sorted imports
- Build isort command with configuration options (profile, line-length, etc.)
- Detect isort version
- Find isort configuration files (pyproject.toml, setup.cfg, .isort.cfg)
- Generate fix commands (without --check-only flag)
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from anvil.models.validator import Issue, ValidationResult


class IsortParser:
    """Parser for isort import sorting output."""

    @staticmethod
    def parse_text(text_output: str, files: List[Path]) -> ValidationResult:
        """
        Parse isort text output into ValidationResult.

        Args:
            text_output: The text output from isort
            files: List of files that were checked

        Returns:
            ValidationResult with any import sorting issues found
        """
        errors = []
        warnings = []

        # Parse ERROR messages for incorrectly sorted imports
        # Pattern: ERROR: /path/to/file.py Imports are incorrectly sorted and/or formatted.
        error_pattern = re.compile(r"ERROR:\s+(.+?)\s+Imports are incorrectly sorted", re.MULTILINE)

        for match in error_pattern.finditer(text_output):
            file_path_str = match.group(1).strip()
            file_path = Path(file_path_str)

            issue = Issue(
                file_path=file_path,
                line_number=1,
                column_number=None,
                severity="error",
                message="Imports are incorrectly sorted and/or formatted",
                rule_name="ISORT_ORDER",
                error_code="ISORT_ORDER",
            )
            errors.append(issue)

        passed = len(errors) == 0 and len(warnings) == 0

        return ValidationResult(
            validator_name="isort",
            passed=passed,
            errors=errors,
            warnings=warnings,
            files_checked=len(files),
        )

    @staticmethod
    def build_command(files: List[Path], config: Dict) -> List[str]:
        """
        Build isort command with configuration options.

        Args:
            files: List of files to check
            config: Configuration options for isort

        Returns:
            Command as list of strings

        Supported config options:
        - profile: str (e.g., "black", "google", "django")
        - line_length: int
        - multi_line_output: int (0-10, different styles)
        - skip: List[str] (patterns to skip)
        - force_single_line: bool
        - diff: bool (show diff output)
        """
        cmd = ["python", "-m", "isort", "--check-only"]

        # Add profile option
        if "profile" in config:
            cmd.extend(["--profile", str(config["profile"])])

        # Add line length
        if "line_length" in config:
            cmd.extend(["--line-length", str(config["line_length"])])

        # Add multi-line output style
        if "multi_line_output" in config:
            cmd.extend(["--multi-line", str(config["multi_line_output"])])

        # Add skip patterns
        if "skip" in config:
            for pattern in config["skip"]:
                cmd.extend(["--skip", pattern])

        # Add force single line imports
        if config.get("force_single_line", False):
            cmd.append("--force-single-line-imports")

        # Add diff output
        if config.get("diff", False):
            cmd.append("--diff")

        # Add files
        cmd.extend([str(f) for f in files])

        return cmd

    @staticmethod
    def run_isort(files: List[Path], config: Dict, timeout: int = 60) -> str:
        """
        Execute isort and return combined output.

        Args:
            files: List of files to check
            config: Configuration options
            timeout: Timeout in seconds

        Returns:
            Combined stdout and stderr as string

        Raises:
            FileNotFoundError: If isort is not installed
            subprocess.TimeoutExpired: If execution exceeds timeout
        """
        cmd = IsortParser.build_command(files, config)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # Combine stdout and stderr, handling None values
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        output = stdout + "\n" + stderr

        return output.strip()

    @staticmethod
    def run_and_parse(files: List[Path], config: Dict, timeout: int = 60) -> ValidationResult:
        """
        Run isort and parse results.

        Args:
            files: List of files to check
            config: Configuration options
            timeout: Timeout in seconds

        Returns:
            ValidationResult with import sorting issues
        """
        output = IsortParser.run_isort(files, config, timeout)
        return IsortParser.parse_text(output, files)

    @staticmethod
    def get_version() -> Optional[str]:
        """
        Get isort version.

        Returns:
            Version string or None if detection fails
        """
        try:
            result = subprocess.run(
                ["python", "-m", "isort", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Extract version from output like "VERSION 5.13.2"
                version_match = re.search(r"VERSION\s+(\d+\.\d+\.\d+)", result.stdout)
                if version_match:
                    return version_match.group(1)

                # Fallback: try to extract any version-like string
                version_match = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
                if version_match:
                    return version_match.group(1)

            return None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    @staticmethod
    def find_config_file(directory: Path) -> Optional[Path]:
        """
        Find isort configuration file in directory.

        Searches for (in order):
        1. pyproject.toml with [tool.isort] section
        2. setup.cfg with [isort] section
        3. .isort.cfg

        Args:
            directory: Directory to search in

        Returns:
            Path to config file or None if not found
        """
        # Check pyproject.toml
        pyproject = directory / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "[tool.isort]" in content:
                return pyproject

        # Check setup.cfg
        setup_cfg = directory / "setup.cfg"
        if setup_cfg.exists():
            content = setup_cfg.read_text()
            if "[isort]" in content:
                return setup_cfg

        # Check .isort.cfg
        isort_cfg = directory / ".isort.cfg"
        if isort_cfg.exists():
            return isort_cfg

        return None

    @staticmethod
    def generate_fix_command(files: List[Path], config: Dict) -> List[str]:
        """
        Generate command to fix import sorting issues.

        This is the same as build_command but without --check-only flag,
        so isort will actually reformat the files.

        Args:
            files: List of files to fix
            config: Configuration options

        Returns:
            Command as list of strings
        """
        cmd = ["python", "-m", "isort"]

        # Add profile option
        if "profile" in config:
            cmd.extend(["--profile", str(config["profile"])])

        # Add line length
        if "line_length" in config:
            cmd.extend(["--line-length", str(config["line_length"])])

        # Add multi-line output style
        if "multi_line_output" in config:
            cmd.extend(["--multi-line", str(config["multi_line_output"])])

        # Add skip patterns
        if "skip" in config:
            for pattern in config["skip"]:
                cmd.extend(["--skip", pattern])

        # Add force single line imports
        if config.get("force_single_line", False):
            cmd.append("--force-single-line-imports")

        # Add diff output (helpful to see what will change)
        if config.get("diff", False):
            cmd.append("--diff")

        # Add files
        cmd.extend([str(f) for f in files])

        return cmd
