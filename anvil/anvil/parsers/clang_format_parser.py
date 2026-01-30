"""
Parser for clang-format C++ code formatter.

This parser executes clang-format in dry-run mode to check if C++ files
are properly formatted according to a specified style (Google, LLVM, etc.).
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from anvil.models.validator import Issue, ValidationResult


class ClangFormatParser:
    """
    Parser for clang-format output.

    Executes clang-format in dry-run mode with --Werror flag to detect
    formatting issues. Supports multiple output formats including XML.
    """

    def parse_output(self, output: str, files: List[str], exit_code: int = 0) -> ValidationResult:
        """
        Parse clang-format output.

        In dry-run mode with --Werror, clang-format returns:
        - exit code 0: all files properly formatted
        - exit code 1: at least one file needs formatting

        Args:
            output: The stdout/stderr from clang-format
            files: List of files that were checked
            exit_code: The exit code from clang-format command

        Returns:
            ValidationResult with errors for files needing formatting
        """
        errors = []
        warnings = []

        # Check for XML replacements output
        if output.strip().startswith("<?xml"):
            errors.extend(self._parse_xml_replacements(output, files))
        # Check for diff output
        elif "---" in output and "+++" in output:
            errors.extend(self._parse_diff_output(output, files))
        # Exit code-based detection (default dry-run mode)
        elif exit_code != 0:
            # With --dry-run --Werror, exit code 1 means formatting needed
            # Without more detailed output, we report all files as potentially needing formatting
            for file_path in files:
                errors.append(
                    Issue(
                        file_path=file_path,
                        line_number=0,
                        column_number=None,
                        message="File needs formatting",
                        rule_name="formatting",
                        error_code="clang-format",
                        severity="error",
                    )
                )

        # All files properly formatted
        passed = len(errors) == 0

        return ValidationResult(
            validator_name="clang-format",
            passed=passed,
            errors=errors,
            warnings=warnings,
            execution_time=0.0,
            files_checked=len(files),
        )

    def _parse_xml_replacements(self, xml_output: str, files: List[str]) -> List[Issue]:
        """
        Parse XML replacements format.

        Args:
            xml_output: XML output from --output-replacements-xml
            files: List of files checked

        Returns:
            List of issues found in XML
        """
        errors = []

        # Extract replacement tags
        replacement_pattern = r"<replacement offset=\'\d+\' length=\'\d+\' file=\'([^\']+)\'>"
        matches = re.findall(replacement_pattern, xml_output)

        # Group by file
        files_needing_formatting = set(matches)

        for file_path in files_needing_formatting:
            errors.append(
                Issue(
                    file_path=file_path,
                    line_number=0,
                    column_number=None,
                    message="File needs formatting (detected via XML replacements)",
                    rule_name="formatting",
                    error_code="clang-format-xml",
                    severity="error",
                )
            )

        return errors

    def _parse_diff_output(self, diff_output: str, files: List[str]) -> List[Issue]:
        """
        Parse diff output format.

        Args:
            diff_output: Diff output showing formatting changes
            files: List of files checked

        Returns:
            List of issues found in diff
        """
        errors = []

        # Extract file names from diff headers (--- filename)
        file_pattern = r"^---\s+(.+)$"
        matches = re.findall(file_pattern, diff_output, re.MULTILINE)

        files_needing_formatting = set(matches)

        for file_path in files_needing_formatting:
            errors.append(
                Issue(
                    file_path=file_path,
                    line_number=0,
                    column_number=None,
                    message="File needs formatting (detected via diff)",
                    rule_name="formatting",
                    error_code="clang-format-diff",
                    severity="error",
                )
            )

        return errors

    def build_command(self, files: List[str], options: Dict) -> List[str]:
        """
        Build clang-format command with options.

        Args:
            files: List of files to check
            options: Configuration options

        Returns:
            Command as list of strings
        """
        cmd = ["clang-format"]

        # Style option (Google, LLVM, file, etc.)
        style = options.get("style", "Google")
        cmd.append(f"--style={style}")

        # Fallback style when using file-based style
        if "fallback_style" in options:
            cmd.append(f"--fallback-style={options['fallback_style']}")

        # XML replacements output
        if options.get("output_replacements_xml", False):
            cmd.append("--output-replacements-xml")

        # Assume filename (for stdin mode)
        if "assume_filename" in options:
            cmd.append(f"--assume-filename={options['assume_filename']}")

        # Dry-run mode (default for checking)
        if options.get("dry_run", True):
            cmd.append("--dry-run")

        # Werror flag (treat formatting issues as errors)
        if options.get("werror", True):
            cmd.append("--Werror")

        # Add files
        cmd.extend(files)

        return cmd

    def run(
        self, files: List[str], options: Dict, timeout: Optional[int] = None
    ) -> ValidationResult:
        """
        Run clang-format and parse results.

        Args:
            files: List of files to check
            options: Configuration options
            timeout: Command timeout in seconds

        Returns:
            ValidationResult with formatting issues

        Raises:
            FileNotFoundError: If clang-format not installed
            subprocess.TimeoutExpired: If command times out
        """
        cmd = self.build_command(files, options)

        if timeout is None:
            timeout = options.get("timeout", 300)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return self.parse_output(result.stdout + result.stderr, files, result.returncode)

    def get_version(self) -> Optional[str]:
        """
        Get clang-format version.

        Returns:
            Version string or None if not available
        """
        try:
            result = subprocess.run(
                ["clang-format", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Extract version from output
            # Format: "clang-format version 14.0.0" or "LLVM version 15.0.7"
            version_match = re.search(r"version\s+(\d+\.\d+\.\d+)", result.stdout)
            if version_match:
                return version_match.group(1)

            # Fallback: return first line
            return result.stdout.split("\n")[0].strip()

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    def detect_config_file(self, directory: Path) -> Optional[Path]:
        """
        Detect .clang-format configuration file.

        Searches current directory and up to 10 parent directories
        for .clang-format or _clang-format files.

        Args:
            directory: Starting directory for search

        Returns:
            Path to config file or None
        """
        current = Path(directory).resolve()

        # Search up to 10 levels
        for _ in range(10):
            # Check for .clang-format
            config_file = current / ".clang-format"
            if config_file.exists():
                return config_file

            # Check for _clang-format variant
            config_file = current / "_clang-format"
            if config_file.exists():
                return config_file

            # Move to parent directory
            parent = current.parent
            if parent == current:  # Reached root
                break
            current = parent

        return None

    def generate_fix_command(self, files: List[str], options: Dict) -> str:
        """
        Generate command to fix formatting issues.

        Args:
            files: List of files to format
            options: Configuration options

        Returns:
            Command string to fix issues
        """
        cmd = ["clang-format", "-i"]  # -i for in-place editing

        # Style option
        style = options.get("style", "Google")
        cmd.append(f"--style={style}")

        # Fallback style
        if "fallback_style" in options:
            cmd.append(f"--fallback-style={options['fallback_style']}")

        # Add files
        cmd.extend(files)

        return " ".join(cmd)
