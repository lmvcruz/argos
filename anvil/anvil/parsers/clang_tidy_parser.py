"""
Parser for clang-tidy YAML output.

Parses YAML diagnostic output from clang-tidy with fix suggestions.
"""

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from anvil.models.validator import Issue, ValidationResult


class ClangTidyParser:
    """
    Static parser for clang-tidy YAML output.

    Parses clang-tidy diagnostics including warnings, errors, and fix suggestions.
    """

    @staticmethod
    def parse_yaml(
        yaml_output: str,
        files: List[Path],
        config: Dict[str, Any],
    ) -> ValidationResult:
        """
        Parse clang-tidy YAML output into ValidationResult.

        Args:
            yaml_output: YAML output from clang-tidy --export-fixes
            files: List of files that were analyzed
            config: Configuration dictionary for parsing options

        Returns:
            ValidationResult with errors and warnings from diagnostics
        """
        errors = []
        warnings = []

        try:
            # Parse YAML documents (clang-tidy can output multiple YAML docs)
            docs = list(yaml.safe_load_all(yaml_output))

            for doc in docs:
                if not doc or "Diagnostics" not in doc:
                    continue

                diagnostics = doc.get("Diagnostics", [])

                for diagnostic in diagnostics:
                    issue = ClangTidyParser._parse_diagnostic(diagnostic, files)
                    if issue:
                        if issue.severity == "error":
                            errors.append(issue)
                        else:
                            warnings.append(issue)

        except yaml.YAMLError as e:
            errors.append(
                Issue(
                    file_path=str(files[0] if files else Path(".")),
                    line_number=0,
                    column_number=None,
                    severity="error",
                    message=f"Failed to parse clang-tidy YAML output: {e}",
                    rule_name="yaml-parse-error",
                    error_code=None,
                )
            )

        # Fail if there are errors or warnings
        passed = len(errors) == 0 and len(warnings) == 0

        return ValidationResult(
            validator_name="clang-tidy",
            passed=passed,
            errors=errors,
            warnings=warnings,
            files_checked=files,
        )

    @staticmethod
    def _parse_diagnostic(
        diagnostic: Dict[str, Any],
        files: List[Path],
    ) -> Optional[Issue]:
        """
        Parse a single diagnostic entry into an Issue.

        Args:
            diagnostic: Diagnostic dictionary from YAML
            files: List of files being analyzed

        Returns:
            Issue object or None if diagnostic cannot be parsed
        """
        try:
            diag_name = diagnostic.get("DiagnosticName", "unknown")
            level = diagnostic.get("Level", "Warning")
            diag_message = diagnostic.get("DiagnosticMessage", {})

            message = diag_message.get("Message", "")
            file_path_str = diag_message.get("FilePath", "")
            file_offset = diag_message.get("FileOffset", 0)

            # Convert file path to Path object
            if file_path_str:
                file_path = Path(file_path_str)
            elif files:
                file_path = files[0]
            else:
                file_path = Path(".")

            # Convert file offset to line/column if file exists
            line_number, column_number = ClangTidyParser._convert_offset_to_line(
                file_path, file_offset
            )

            # Map clang-tidy level to severity
            severity = ClangTidyParser._map_level_to_severity(level)

            return Issue(
                file_path=str(file_path),
                line_number=line_number,
                column_number=column_number,
                severity=severity,
                message=f"{diag_name}: {message}",
                rule_name=diag_name,
                error_code=None,
            )

        except (KeyError, TypeError):
            # If diagnostic is malformed, return None
            return None

    @staticmethod
    def _convert_offset_to_line(
        file_path: Path,
        offset: int,
    ) -> Tuple[int, int]:
        """
        Convert file offset to line and column numbers.

        Args:
            file_path: Path to the file
            offset: Byte offset in file

        Returns:
            Tuple of (line_number, column_number)
        """
        if not file_path.exists():
            return (0, 0)

        try:
            with open(file_path, "rb") as f:
                content = f.read(offset)

            # Count newlines to get line number
            line_number = content.count(b"\n") + 1

            # Find column by getting distance from last newline
            last_newline = content.rfind(b"\n")
            if last_newline == -1:
                column_number = offset + 1
            else:
                column_number = offset - last_newline

            return (line_number, column_number)

        except (IOError, OSError):
            return (0, 0)

    @staticmethod
    def _map_level_to_severity(level: str) -> str:
        """
        Map clang-tidy diagnostic level to severity string.

        Args:
            level: Diagnostic level string (Error, Warning, Note)

        Returns:
            Severity string ("error", "warning", "info")
        """
        level_lower = level.lower()

        if level_lower == "error":
            return "error"
        elif level_lower in ("warning", "note"):
            return "warning"
        else:
            return "warning"

    @staticmethod
    def count_fixable_diagnostics(yaml_output: str) -> int:
        """
        Count diagnostics that have fix suggestions (replacements).

        Args:
            yaml_output: YAML output from clang-tidy

        Returns:
            Number of diagnostics with replacements
        """
        try:
            docs = list(yaml.safe_load_all(yaml_output))
            count = 0

            for doc in docs:
                if not doc or "Diagnostics" not in doc:
                    continue

                for diagnostic in doc.get("Diagnostics", []):
                    diag_message = diagnostic.get("DiagnosticMessage", {})
                    replacements = diag_message.get("Replacements", [])

                    if replacements:
                        count += 1

            return count

        except yaml.YAMLError:
            return 0

    @staticmethod
    def build_command(
        files: List[Path],
        config: Dict[str, Any],
    ) -> List[str]:
        """
        Build clang-tidy command with configuration options.

        Args:
            files: List of files to analyze
            config: Configuration dictionary with options

        Returns:
            Command list for subprocess execution
        """
        command = ["clang-tidy"]

        # Add checks option if specified and no config file
        if "checks" in config and not config.get("config_file"):
            command.append(f"--checks={config['checks']}")

        # Add header filter if specified
        if "header_filter" in config:
            command.append(f"--header-filter={config['header_filter']}")

        # Add warnings-as-errors if specified
        if "warnings_as_errors" in config:
            command.append(f"--warnings-as-errors={config['warnings_as_errors']}")

        # Add export-fixes for YAML output
        command.append("--export-fixes=-")

        # Add compile commands database path if specified
        if "compile_commands" in config:
            command.append(f"-p={config['compile_commands']}")

        # Add files
        for file in files:
            command.append(str(file))

        # Add extra compiler arguments after --
        if "extra_args" in config:
            command.append("--")
            command.extend(config["extra_args"])

        return command

    @staticmethod
    def run_clang_tidy(
        files: List[Path],
        config: Dict[str, Any],
        timeout: int = 300,
    ) -> subprocess.CompletedProcess:
        """
        Execute clang-tidy subprocess.

        Args:
            files: List of files to analyze
            config: Configuration dictionary
            timeout: Timeout in seconds (default 300)

        Returns:
            CompletedProcess with stdout and stderr
        """
        command = ClangTidyParser.build_command(files, config)
        timeout = config.get("timeout", timeout)

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return result

    @staticmethod
    def run_and_parse(
        files: List[Path],
        config: Dict[str, Any],
    ) -> ValidationResult:
        """
        Execute clang-tidy and parse output.

        Args:
            files: List of files to analyze
            config: Configuration dictionary

        Returns:
            ValidationResult with parsed diagnostics
        """
        try:
            result = ClangTidyParser.run_clang_tidy(files, config)

            # Parse YAML output from stdout
            return ClangTidyParser.parse_yaml(result.stdout, files, config)

        except FileNotFoundError:
            return ValidationResult(
                validator_name="clang-tidy",
                passed=False,
                errors=[
                    Issue(
                        file_path=str(files[0] if files else Path(".")),
                        line_number=0,
                        column_number=None,
                        severity="error",
                        message="clang-tidy is not installed or not in PATH",
                        rule_name="tool-not-found",
                        error_code=None,
                    )
                ],
                warnings=[],
                files_checked=files,
            )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                validator_name="clang-tidy",
                passed=False,
                errors=[
                    Issue(
                        file_path=str(files[0] if files else Path(".")),
                        line_number=0,
                        column_number=None,
                        severity="error",
                        message=(
                            f"clang-tidy execution timed out after "
                            f"{config.get('timeout', 300)} seconds"
                        ),
                        rule_name="execution-timeout",
                        error_code=None,
                    )
                ],
                warnings=[],
                files_checked=files,
            )

    @staticmethod
    def get_version() -> Optional[str]:
        """
        Detect clang-tidy version.

        Returns:
            Version string or None if detection fails
        """
        try:
            result = subprocess.run(
                ["clang-tidy", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            # Extract version from output like "LLVM version 14.0.0"
            match = re.search(r"LLVM version ([\d.]+)", result.stdout)
            if match:
                return match.group(1)

            return None

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    @staticmethod
    def is_installed() -> bool:
        """
        Check if clang-tidy is installed.

        Returns:
            True if clang-tidy is available, False otherwise
        """
        return ClangTidyParser.get_version() is not None

    @staticmethod
    def group_by_check_name(yaml_output: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group diagnostics by check name.

        Args:
            yaml_output: YAML output from clang-tidy

        Returns:
            Dictionary mapping check names to list of diagnostics
        """
        grouped = {}

        try:
            docs = list(yaml.safe_load_all(yaml_output))

            for doc in docs:
                if not doc or "Diagnostics" not in doc:
                    continue

                for diagnostic in doc.get("Diagnostics", []):
                    check_name = diagnostic.get("DiagnosticName", "unknown")

                    if check_name not in grouped:
                        grouped[check_name] = []

                    grouped[check_name].append(diagnostic)

        except yaml.YAMLError:
            pass

        return grouped

    @staticmethod
    def group_by_file(yaml_output: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group diagnostics by file path.

        Args:
            yaml_output: YAML output from clang-tidy

        Returns:
            Dictionary mapping file paths to list of diagnostics
        """
        grouped = {}

        try:
            docs = list(yaml.safe_load_all(yaml_output))

            for doc in docs:
                if not doc or "Diagnostics" not in doc:
                    continue

                for diagnostic in doc.get("Diagnostics", []):
                    diag_message = diagnostic.get("DiagnosticMessage", {})
                    file_path = diag_message.get("FilePath", "unknown")

                    if file_path not in grouped:
                        grouped[file_path] = []

                    grouped[file_path].append(diagnostic)

        except yaml.YAMLError:
            pass

        return grouped

    @staticmethod
    def filter_by_severity(yaml_output: str, severity: str) -> List[Dict[str, Any]]:
        """
        Filter diagnostics by severity level.

        Args:
            yaml_output: YAML output from clang-tidy
            severity: Severity level to filter (Error, Warning, Note)

        Returns:
            List of diagnostics matching the severity
        """
        filtered = []

        try:
            docs = list(yaml.safe_load_all(yaml_output))

            for doc in docs:
                if not doc or "Diagnostics" not in doc:
                    continue

                for diagnostic in doc.get("Diagnostics", []):
                    if diagnostic.get("Level", "").lower() == severity.lower():
                        filtered.append(diagnostic)

        except yaml.YAMLError:
            pass

        return filtered

    @staticmethod
    def find_config_file(directory: Path) -> Optional[Path]:
        """
        Find .clang-tidy configuration file.

        Searches current directory and parent directories.

        Args:
            directory: Starting directory for search

        Returns:
            Path to .clang-tidy file or None if not found
        """
        current = directory.resolve()

        # Search up to root directory
        while current != current.parent:
            config_file = current / ".clang-tidy"
            if config_file.exists():
                return config_file

            current = current.parent

        # Check root directory
        config_file = current / ".clang-tidy"
        if config_file.exists():
            return config_file

        return None
