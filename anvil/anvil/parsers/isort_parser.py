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

import logging
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from anvil.models.validator import Issue, ValidationResult

# Set up logger for anvil.isort.parser
logger = logging.getLogger('anvil.isort.parser')


class IsortParser:
    """Parser for isort import sorting output."""

    @staticmethod
    def parse_text(text_output: str, files: List[Path], diff_output: Optional[str] = None) -> ValidationResult:
        """
        Parse isort text output into ValidationResult.

        Args:
            text_output: The text output from isort
            files: List of files that were checked
            diff_output: Optional diff output from isort --diff

        Returns:
            ValidationResult with any import sorting issues found
        """
        errors = []
        warnings = []

        # Parse ERROR messages for incorrectly sorted imports
        # Pattern: ERROR: /path/to/file.py Imports are incorrectly sorted and/or formatted.
        error_pattern = re.compile(
            r"ERROR:\s+(.+?)\s+Imports are incorrectly sorted", re.MULTILINE)

        for match in error_pattern.finditer(text_output):
            file_path_str = match.group(1).strip()
            file_path = Path(file_path_str)
            logger.debug(
                f"IsortParser.parse_text: found ERROR for {file_path_str}")

            # Try to extract diff for this file from diff_output
            file_diff = None
            if diff_output:
                logger.debug(
                    f"IsortParser: diff_output available, length={len(diff_output)}")
                logger.debug(
                    f"IsortParser: searching for file {file_path_str}")

                # isort outputs diff with format: --- a/<path>, --- <path>, or --- path\with\backslashes
                # We need to normalize the path for regex and try multiple variations

                # Get the filename from the path
                filename = Path(file_path_str).name
                logger.debug(f"IsortParser: extracted filename: {filename}")

                # Try multiple patterns to match the diff header
                patterns_to_try = [
                    # Forward slashes with a/ prefix (standard Unix diff)
                    rf"--- a/{re.escape(file_path_str.replace(chr(92), '/'))}.*?(?=--- |\Z)",
                    # Forward slashes without prefix
                    rf"--- {re.escape(file_path_str.replace(chr(92), '/'))}.*?(?=--- |\Z)",
                    # Backslashes with a/ prefix
                    rf"--- a/{re.escape(file_path_str)}.*?(?=--- |\Z)",
                    # Backslashes without prefix
                    rf"--- {re.escape(file_path_str)}.*?(?=--- |\Z)",
                    # Just match the filename as fallback
                    rf"--- .+?{re.escape(filename)}.*?(?=--- |\Z)",
                ]

                for i, pattern_str in enumerate(patterns_to_try):
                    diff_pattern = re.compile(
                        pattern_str, re.MULTILINE | re.DOTALL)
                    diff_match = diff_pattern.search(diff_output)
                    if diff_match:
                        file_diff = diff_match.group(0).strip()
                        logger.debug(
                            f"IsortParser: extracted diff using pattern #{i+1}, length={len(file_diff)}")
                        break

                if not file_diff:
                    logger.debug(
                        f"IsortParser: NO diff found for {file_path_str}, tried {len(patterns_to_try)} patterns")
                    logger.debug(
                        f"IsortParser: sample of diff_output (first 500 chars):\n{diff_output[:500]}")
            else:
                logger.debug(f"IsortParser: NO diff_output provided")

            issue = Issue(
                file_path=file_path,
                line_number=1,
                column_number=None,
                severity="error",
                message="Imports are incorrectly sorted and/or formatted",
                rule_name="ISORT_ORDER",
                error_code="ISORT_ORDER",
                diff=file_diff,
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
    def run_isort(files: List[Path], config: Dict, timeout: int = 60) -> tuple:
        """
        Execute isort and return combined output and diff output.

        Args:
            files: List of files to check
            config: Configuration options
            timeout: Timeout in seconds

        Returns:
            Tuple of (combined output, diff output)

        Raises:
            FileNotFoundError: If isort is not installed
            subprocess.TimeoutExpired: If execution exceeds timeout
        """
        # Add diff to config for the build_command
        config_with_diff = config.copy()
        config_with_diff["diff"] = True

        cmd = IsortParser.build_command(files, config_with_diff)

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

        return output.strip(), stdout

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
        logger.info(
            f"IsortParser.run_and_parse: starting for {len(files)} files")
        logger.debug(
            f"IsortParser.run_and_parse: files={[str(f) for f in files]}, config={config}")

        output, diff_output = IsortParser.run_isort(files, config, timeout)

        logger.debug(f"IsortParser: isort command executed")
        logger.debug(
            f"IsortParser: text output length={len(output)}, diff output length={len(diff_output) if diff_output else 0}")

        result = IsortParser.parse_text(output, files, diff_output)

        logger.info(
            f"IsortParser: parsing complete, {len(result.errors)} errors found")
        if result.errors:
            for error in result.errors:
                if hasattr(error, 'diff') and error.diff:
                    logger.debug(
                        f"IsortParser: error for {error.file_path} has diff (length={len(error.diff)})")
                else:
                    logger.debug(
                        f"IsortParser: error for {error.file_path} has NO diff")

        return result

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
                version_match = re.search(
                    r"VERSION\s+(\d+\.\d+\.\d+)", result.stdout)
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
