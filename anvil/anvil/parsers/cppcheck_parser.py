"""
Parser for cppcheck XML output.

Cppcheck is a static analysis tool for C/C++ code that detects bugs, undefined
behavior, dangerous coding constructs, and code quality issues.
"""

import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

from anvil.models.validator import Issue, ValidationResult


class CppcheckParser:
    """
    Parser for cppcheck XML output (version 2 format).

    Cppcheck detects various issue types:
    - error: Bugs and undefined behavior
    - warning: Suspicious code that might be bugs
    - style: Style issues and code cleanup suggestions
    - performance: Performance optimization suggestions
    - portability: Portability issues
    - information: Informational messages

    Example XML output:
    <?xml version="1.0" encoding="UTF-8"?>
    <results version="2">
    <cppcheck version="2.10"/>
    <errors>
    <error id="nullPointer" severity="error" msg="Null pointer dereference">
    <location file="main.cpp" line="42" column="5"/>
    </error>
    </errors>
    </results>
    """

    # Severity mapping from cppcheck to Anvil
    SEVERITY_MAP = {
        "error": "error",
        "warning": "warning",
        "style": "warning",
        "performance": "warning",
        "portability": "warning",
        "information": "info",
    }

    @staticmethod
    def parse_xml(
        xml_output: str,
        files: List[Path],
        config: Dict[str, Any],
    ) -> ValidationResult:
        """
        Parse cppcheck XML output and extract issues.

        Args:
            xml_output: XML output string from cppcheck
            files: List of files that were analyzed
            config: Configuration dictionary

        Returns:
            ValidationResult with parsed issues
        """
        errors: List[Issue] = []
        warnings: List[Issue] = []

        try:
            root = ET.fromstring(xml_output)

            # Find all error elements
            for error_elem in root.findall(".//error"):
                issue = CppcheckParser._parse_error_element(error_elem)
                if issue:
                    if issue.severity == "error":
                        errors.append(issue)
                    else:
                        warnings.append(issue)

        except ET.ParseError as e:
            errors.append(
                Issue(
                    file_path=str(files[0] if files else Path(".")),
                    line_number=0,
                    column_number=None,
                    severity="error",
                    message=f"Failed to parse cppcheck XML output: {e}",
                    rule_name="xml-parse-error",
                    error_code=None,
                )
            )

        # Fail if there are errors or warnings (based on configuration)
        passed = len(errors) == 0 and len(warnings) == 0

        return ValidationResult(
            validator_name="cppcheck",
            passed=passed,
            errors=errors,
            warnings=warnings,
            files_checked=len(files),
        )

    @staticmethod
    def _parse_error_element(error_elem: ET.Element) -> Optional[Issue]:
        """
        Parse a single error element from XML.

        Args:
            error_elem: XML element for error

        Returns:
            Issue object or None if parsing failed
        """
        try:
            error_id = error_elem.get("id", "unknown")
            severity = error_elem.get("severity", "error")
            msg = error_elem.get("msg", "No message")
            inconclusive = error_elem.get("inconclusive", "false") == "true"
            cwe = error_elem.get("cwe")

            # Get first location (primary location)
            location = error_elem.find("location")
            if location is None:
                return None

            file_path = location.get("file", "unknown")
            line = int(location.get("line", "0"))
            column_str = location.get("column")
            column = int(column_str) if column_str else None

            # Map cppcheck severity to Anvil severity
            mapped_severity = CppcheckParser.SEVERITY_MAP.get(severity, "warning")

            # Build message
            message = f"{error_id}: {msg}"
            if inconclusive:
                message += " (inconclusive)"

            # Build error code (include CWE if available)
            error_code = f"CWE-{cwe}" if cwe else None

            return Issue(
                file_path=file_path,
                line_number=line,
                column_number=column,
                severity=mapped_severity,
                message=message,
                rule_name=error_id,
                error_code=error_code,
            )

        except (KeyError, TypeError, ValueError):
            # If error element is malformed, return None
            return None

    @staticmethod
    def build_command(
        files: List[Path],
        config: Dict[str, Any],
    ) -> List[str]:
        """
        Build cppcheck command with configuration options.

        Args:
            files: List of files to analyze
            config: Configuration dictionary with options:
                - enable: List of check categories to enable
                - suppress: List of error IDs to suppress
                - std: C++ standard (c++11, c++14, c++17, c++20, etc.)
                - platform: Platform (unix32, unix64, win32, win64, etc.)
                - includes: List of include paths
                - defines: List of preprocessor defines
                - inconclusive: Enable inconclusive checks (bool)
                - timeout: Timeout in seconds (default 300)

        Returns:
            Command as list of strings
        """
        command = ["cppcheck", "--xml", "--xml-version=2"]

        # Enable check categories
        if "enable" in config:
            categories = config["enable"]
            if isinstance(categories, list):
                command.append(f"--enable={','.join(categories)}")
            else:
                command.append(f"--enable={categories}")

        # Suppressions
        if "suppress" in config:
            suppressions = config["suppress"]
            if isinstance(suppressions, list):
                for suppression in suppressions:
                    command.append(f"--suppress={suppression}")
            else:
                command.append(f"--suppress={suppressions}")

        # C++ standard
        if "std" in config:
            command.append(f"--std={config['std']}")

        # Platform
        if "platform" in config:
            command.append(f"--platform={config['platform']}")

        # Include paths
        if "includes" in config:
            for include in config["includes"]:
                command.append(f"-I{include}")

        # Preprocessor defines
        if "defines" in config:
            for define in config["defines"]:
                command.append(f"-D{define}")

        # Inconclusive checks
        if config.get("inconclusive"):
            command.append("--inconclusive")

        # Add files
        for file in files:
            command.append(str(file))

        return command

    @staticmethod
    def run_cppcheck(
        files: List[Path],
        config: Dict[str, Any],
        timeout: int = 300,
    ) -> subprocess.CompletedProcess:
        """
        Execute cppcheck subprocess.

        Args:
            files: List of files to analyze
            config: Configuration dictionary
            timeout: Timeout in seconds (default 300)

        Returns:
            CompletedProcess with stdout and stderr
        """
        command = CppcheckParser.build_command(files, config)
        timeout = config.get("timeout", timeout)

        # Cppcheck outputs to stderr by default
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
        Execute cppcheck and parse output.

        Args:
            files: List of files to analyze
            config: Configuration dictionary

        Returns:
            ValidationResult with parsed issues
        """
        try:
            result = CppcheckParser.run_cppcheck(files, config)

            # Cppcheck outputs XML to stderr
            return CppcheckParser.parse_xml(result.stderr, files, config)

        except FileNotFoundError:
            return ValidationResult(
                validator_name="cppcheck",
                passed=False,
                errors=[
                    Issue(
                        file_path=str(files[0] if files else Path(".")),
                        line_number=0,
                        column_number=None,
                        severity="error",
                        message="cppcheck is not installed or not in PATH",
                        rule_name="tool-not-found",
                        error_code=None,
                    )
                ],
                warnings=[],
                files_checked=files,
            )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                validator_name="cppcheck",
                passed=False,
                errors=[
                    Issue(
                        file_path=str(files[0] if files else Path(".")),
                        line_number=0,
                        column_number=None,
                        severity="error",
                        message=(
                            f"cppcheck execution timed out after "
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
        Detect cppcheck version.

        Returns:
            Version string or None if detection failed
        """
        try:
            result = subprocess.run(
                ["cppcheck", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            # Output format: "Cppcheck 2.10"
            match = re.search(r"Cppcheck\s+(\d+\.\d+(?:\.\d+)?)", result.stdout)
            if match:
                return match.group(1)

            return None

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    @staticmethod
    def is_installed() -> bool:
        """
        Check if cppcheck is installed and available.

        Returns:
            True if cppcheck is available, False otherwise
        """
        return CppcheckParser.get_version() is not None

    @staticmethod
    def group_by_error_id(xml_output: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group errors by error ID (e.g., nullPointer, memleak).

        Args:
            xml_output: XML output from cppcheck

        Returns:
            Dictionary mapping error ID to list of error dictionaries
        """
        grouped: Dict[str, List[Dict[str, Any]]] = {}

        try:
            root = ET.fromstring(xml_output)

            for error_elem in root.findall(".//error"):
                error_id = error_elem.get("id", "unknown")
                if error_id not in grouped:
                    grouped[error_id] = []

                error_dict = {
                    "id": error_id,
                    "severity": error_elem.get("severity"),
                    "msg": error_elem.get("msg"),
                }

                location = error_elem.find("location")
                if location is not None:
                    error_dict["file"] = location.get("file")
                    error_dict["line"] = location.get("line")

                grouped[error_id].append(error_dict)

        except ET.ParseError:
            pass

        return grouped

    @staticmethod
    def group_by_file(xml_output: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group errors by file path.

        Args:
            xml_output: XML output from cppcheck

        Returns:
            Dictionary mapping file path to list of error dictionaries
        """
        grouped: Dict[str, List[Dict[str, Any]]] = {}

        try:
            root = ET.fromstring(xml_output)

            for error_elem in root.findall(".//error"):
                location = error_elem.find("location")
                if location is None:
                    continue

                file_path = str(Path(location.get("file", "unknown")))
                if file_path not in grouped:
                    grouped[file_path] = []

                error_dict = {
                    "id": error_elem.get("id"),
                    "severity": error_elem.get("severity"),
                    "msg": error_elem.get("msg"),
                    "line": location.get("line"),
                }

                grouped[file_path].append(error_dict)

        except ET.ParseError:
            pass

        return grouped

    @staticmethod
    def filter_by_severity(
        xml_output: str,
        severity: str,
    ) -> List[Dict[str, Any]]:
        """
        Filter errors by severity level.

        Args:
            xml_output: XML output from cppcheck
            severity: Severity level to filter by

        Returns:
            List of error dictionaries matching the severity
        """
        filtered: List[Dict[str, Any]] = []

        try:
            root = ET.fromstring(xml_output)

            for error_elem in root.findall(".//error"):
                if error_elem.get("severity") == severity:
                    error_dict = {
                        "id": error_elem.get("id"),
                        "severity": error_elem.get("severity"),
                        "msg": error_elem.get("msg"),
                    }

                    location = error_elem.find("location")
                    if location is not None:
                        error_dict["file"] = location.get("file")
                        error_dict["line"] = location.get("line")

                    filtered.append(error_dict)

        except ET.ParseError:
            pass

        return filtered

    @staticmethod
    def find_suppressions_file(directory: Path) -> Optional[Path]:
        """
        Find cppcheck suppressions file in directory or parent directories.

        Looks for files named:
        - suppressions.txt
        - cppcheck-suppressions.txt
        - .cppcheck-suppressions

        Args:
            directory: Starting directory for search

        Returns:
            Path to suppressions file or None if not found
        """
        current = directory.resolve()

        # Search up to root directory
        while current != current.parent:
            for filename in [
                "suppressions.txt",
                "cppcheck-suppressions.txt",
                ".cppcheck-suppressions",
            ]:
                config_file = current / filename
                if config_file.is_file():
                    return config_file

            current = current.parent

        return None
