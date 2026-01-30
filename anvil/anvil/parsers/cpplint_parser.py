"""
Parser for cpplint output.

This module provides functionality to parse cpplint text output for
Google C++ Style Guide violations.
"""

import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from anvil.models.validator import Issue, ValidationResult


class CpplintParser:
    """
    Parser for cpplint output.

    cpplint is a style checker for C++ that enforces the Google C++ Style Guide.
    It outputs violations in plain text format with file, line, message, category,
    and confidence level.

    Output format:
        file.cpp:line:  message  [category/subcategory] [confidence]

    Example:
        src/main.cpp:10:  Extra space after (  [whitespace/parens] [2]
    """

    # Regex to parse cpplint output lines
    # Format: file.cpp:line:  message  [category/subcategory] [confidence]
    VIOLATION_PATTERN = re.compile(r"^(.+?):(\d+):\s+(.+?)\s+\[([^\]]+)\]\s+\[(\d+)\]")

    def parse_output(self, output: str, files: List[str]) -> ValidationResult:
        """
        Parse cpplint text output into a ValidationResult.

        Args:
            output: Raw text output from cpplint
            files: List of files that were checked

        Returns:
            ValidationResult with parsed issues
        """
        errors = []
        warnings = []

        for line in output.splitlines():
            match = self.VIOLATION_PATTERN.match(line)
            if not match:
                continue

            file_path = match.group(1)
            line_number = int(match.group(2))
            message = match.group(3).strip()
            category = match.group(4)
            confidence = int(match.group(5))

            # Map confidence to severity
            # cpplint confidence: 1 (low) to 5 (high)
            # Confidence 4-5: error (high confidence in violation)
            # Confidence 1-3: warning (lower confidence)
            severity = "error" if confidence >= 4 else "warning"

            issue = Issue(
                file_path=file_path,
                line_number=line_number,
                column_number=None,
                message=message,
                rule_name=category,
                severity=severity,
            )

            if severity == "error":
                errors.append(issue)
            else:
                warnings.append(issue)

        return ValidationResult(
            validator_name="cpplint",
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            files_checked=len(files),
        )

    def build_command(self, files: List[str], options: Dict[str, Any]) -> List[str]:
        """
        Build cpplint command with options.

        Args:
            files: List of files to check
            options: Dictionary of cpplint options

        Returns:
            Command as list of strings

        Supported options:
            - filter: Filter to enable/disable checks (e.g., "-whitespace,+readability")
            - linelength: Maximum line length (default: 80)
            - root: Root directory for header guard calculation
            - extensions: Comma-separated list of file extensions
            - counting: Counting mode (total, toplevel, detailed)
            - quiet: Only print summary (no per-file details)
            - timeout: Execution timeout in seconds
        """
        command = ["cpplint"]

        # Add filter option
        if "filter" in options:
            command.append(f"--filter={options['filter']}")

        # Add line length option
        if "linelength" in options:
            command.append(f"--linelength={options['linelength']}")

        # Add root directory
        if "root" in options:
            command.append(f"--root={options['root']}")

        # Add extensions
        if "extensions" in options:
            command.append(f"--extensions={options['extensions']}")

        # Add counting mode
        if "counting" in options:
            command.append(f"--counting={options['counting']}")

        # Add quiet flag
        if options.get("quiet", False):
            command.append("--quiet")

        # Add files
        command.extend(files)

        return command

    def run(self, files: List[str], options: Dict[str, Any]) -> ValidationResult:
        """
        Run cpplint on files and parse the output.

        Args:
            files: List of files to check
            options: Dictionary of cpplint options

        Returns:
            ValidationResult with parsed issues
        """
        command = self.build_command(files, options)
        timeout = options.get("timeout", 300)  # Default 5 minutes

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            # cpplint writes output to stderr, not stdout
            output = result.stderr if result.stderr else result.stdout

            return self.parse_output(output, files)

        except FileNotFoundError:
            return ValidationResult(
                validator_name="cpplint",
                passed=False,
                errors=[
                    Issue(
                        file_path="",
                        line_number=0,
                        column_number=None,
                        message="cpplint not found. Install with: pip install cpplint",
                        rule_name="tool_not_found",
                        severity="error",
                    )
                ],
                warnings=[],
                files_checked=len(files),
            )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                validator_name="cpplint",
                passed=False,
                errors=[
                    Issue(
                        file_path="",
                        line_number=0,
                        column_number=None,
                        message=f"cpplint timed out after {timeout} seconds",
                        rule_name="timeout",
                        severity="error",
                    )
                ],
                warnings=[],
                files_checked=len(files),
            )

    def get_version(self) -> Optional[str]:
        """
        Get cpplint version.

        Returns:
            Version string or None if not available
        """
        try:
            result = subprocess.run(
                ["cpplint", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            # cpplint outputs version like "cpplint 1.6.1"
            output = result.stdout.strip()
            match = re.search(r"cpplint\s+([\d.]+)", output)
            if match:
                return match.group(1)
            return None

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    def group_by_category(self, issues: List[Issue]) -> Dict[str, List[Issue]]:
        """
        Group issues by top-level category.

        Args:
            issues: List of issues to group

        Returns:
            Dictionary mapping category to list of issues

        Example:
            "whitespace/parens" -> grouped under "whitespace"
            "readability/line_length" -> grouped under "readability"
        """
        grouped: Dict[str, List[Issue]] = defaultdict(list)

        for issue in issues:
            # Extract top-level category (before the slash)
            category = issue.rule_name.split("/")[0]
            grouped[category].append(issue)

        return dict(grouped)

    def group_by_confidence(self, issues: List[Issue]) -> Dict[int, List[Issue]]:
        """
        Group issues by confidence level.

        Note: Confidence is derived from severity:
            - error severity = confidence 4-5
            - warning severity = confidence 1-3

        Args:
            issues: List of issues to group

        Returns:
            Dictionary mapping confidence level to list of issues
        """
        grouped: Dict[int, List[Issue]] = defaultdict(list)

        for issue in issues:
            # Reverse-map severity back to confidence
            # This is an approximation since we don't store exact confidence
            if issue.severity == "error":
                confidence = 4  # Representative value for high confidence
            else:
                confidence = 2  # Representative value for low confidence

            grouped[confidence].append(issue)

        return dict(grouped)

    def get_most_common_violations(
        self, issues: List[Issue], top_n: int = 10
    ) -> List[Tuple[str, int]]:
        """
        Identify the most common violation types.

        Args:
            issues: List of issues to analyze
            top_n: Number of top violations to return

        Returns:
            List of (rule_name, count) tuples, sorted by count descending
        """
        rule_counts = Counter(issue.rule_name for issue in issues)
        return rule_counts.most_common(top_n)

    def detect_config_file(self, directory: Path) -> Optional[Path]:
        """
        Detect cpplint configuration file (CPPLINT.cfg).

        cpplint looks for CPPLINT.cfg in the current directory and parent
        directories up to the repository root.

        Args:
            directory: Directory to start searching from

        Returns:
            Path to CPPLINT.cfg if found, None otherwise
        """
        current = Path(directory).resolve()

        # Search up to 10 levels (reasonable limit)
        for _ in range(10):
            config_file = current / "CPPLINT.cfg"
            if config_file.exists():
                return config_file

            # Stop at filesystem root
            if current.parent == current:
                break

            current = current.parent

        return None
