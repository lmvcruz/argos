"""
CI log parser for Scout.

Parses CI logs from various sources (GitHub Actions, etc.) to extract:
- Test results (pytest, unittest, etc.)
- Coverage data
- Lint violations (flake8, pylint, etc.)
- Failure patterns
"""

import re
from typing import Dict, List, Optional


class CILogParser:
    """
    Parser for CI logs.

    Extracts structured data from CI log output including test results,
    coverage information, lint violations, and failure patterns.
    """

    def parse_pytest_log(self, log_content: str) -> List[Dict]:
        """
        Parse pytest output from CI logs.

        Extracts test results including nodeids, outcomes, durations,
        error messages, and tracebacks.

        Args:
            log_content: Raw pytest log output

        Returns:
            List of test result dictionaries with keys:
            - test_nodeid: Test identifier (e.g., "tests/test_example.py::test_func")
            - outcome: Test outcome ("passed", "failed", "skipped", "error")
            - duration: Test duration in seconds (optional)
            - error_message: Error message for failed tests (optional)
            - error_traceback: Full traceback for failed tests (optional)

        Examples:
            >>> parser = CILogParser()
            >>> results = parser.parse_pytest_log(log_text)
            >>> results[0]["test_nodeid"]
            'tests/test_example.py::test_function'
        """
        if not log_content:
            return []

        results = []

        # Pattern for test result lines:
        # tests/test_example.py::test_function_one PASSED                          [ 20%]
        test_pattern = re.compile(
            r"^(.+?)::([\w\[\],-]+)\s+(PASSED|FAILED|SKIPPED|ERROR)",
            re.MULTILINE,
        )

        # Find all test results
        for match in test_pattern.finditer(log_content):
            filepath = match.group(1).strip()
            test_name = match.group(2)
            outcome = match.group(3).lower()

            test_nodeid = f"{filepath}::{test_name}"

            result = {
                "test_nodeid": test_nodeid,
                "outcome": outcome,
                "duration": None,
                "error_message": None,
                "error_traceback": None,
            }

            results.append(result)

        # Extract failure/error details
        self._extract_failure_details(log_content, results)

        # Extract durations if available
        self._extract_durations(log_content, results)

        return results

    def _extract_failure_details(self, log_content: str, results: List[Dict]) -> None:
        """
        Extract failure details (error messages and tracebacks) from log.

        Args:
            log_content: Raw pytest log output
            results: List of test results to update with failure details
        """
        # Pattern for failure/error sections
        failure_section_pattern = re.compile(
            r"={3,}\s+(FAILURES|ERRORS)\s+={3,}(.*?)(?:={3,}\s+(?:short test summary|FAILURES|ERRORS|\d+ (?:passed|failed))|$)",
            re.DOTALL | re.IGNORECASE,
        )

        for section_match in failure_section_pattern.finditer(log_content):
            section_content = section_match.group(2)

            # Pattern for individual failure entries
            failure_entry_pattern = re.compile(
                r"_{3,}\s+(?:ERROR at setup of |FAILED )?(.+?)\s+_{3,}(.*?)(?=_{3,}|$)",
                re.DOTALL,
            )

            for entry_match in failure_entry_pattern.finditer(section_content):
                test_identifier = entry_match.group(1).strip()
                failure_content = entry_match.group(2).strip()

                # Find matching test in results
                for result in results:
                    if test_identifier in result["test_nodeid"] or result["test_nodeid"].endswith(
                        test_identifier
                    ):
                        # Extract error message (usually after 'E   ')
                        error_lines = re.findall(r"^E\s+(.+)$", failure_content, re.MULTILINE)
                        if error_lines:
                            result["error_message"] = "\n".join(error_lines)

                        # Store full traceback
                        result["error_traceback"] = failure_content
                        break

        # Also check short test summary for quick error messages
        summary_pattern = re.compile(r"^(FAILED|ERROR)\s+(.+?)\s+-\s+(.+)$", re.MULTILINE)

        for summary_match in summary_pattern.finditer(log_content):
            test_nodeid = summary_match.group(2).strip()
            error_msg = summary_match.group(3).strip()

            # Find matching test in results
            for result in results:
                if result["test_nodeid"] == test_nodeid:
                    if not result["error_message"]:
                        result["error_message"] = error_msg
                    break

    def _extract_durations(self, log_content: str, results: List[Dict]) -> None:
        """
        Extract test durations from slowest durations section.

        Args:
            log_content: Raw pytest log output
            results: List of test results to update with durations
        """
        # Pattern for slowest durations section
        duration_pattern = re.compile(r"(\d+\.\d+)s\s+call\s+(.+)$", re.MULTILINE)

        for match in duration_pattern.finditer(log_content):
            duration = float(match.group(1))
            test_nodeid = match.group(2).strip()

            # Find matching test in results
            for result in results:
                if result["test_nodeid"] == test_nodeid:
                    result["duration"] = duration
                    break

    def parse_coverage_log(self, log_content: str) -> Optional[Dict]:
        """
        Parse coverage output from CI logs.

        Extracts coverage percentages, statement counts, and missing lines
        from pytest-cov or coverage.py output.

        Args:
            log_content: Raw coverage log output

        Returns:
            Dictionary with coverage data:
            - total_coverage: Overall coverage percentage
            - total_statements: Total number of statements
            - total_missing: Total number of missing statements
            - modules: List of module coverage data

        Examples:
            >>> parser = CILogParser()
            >>> coverage = parser.parse_coverage_log(log_text)
            >>> coverage["total_coverage"]
            93.0
        """
        if not log_content:
            return None

        # Pattern for coverage table header
        header_pattern = re.compile(r"Name\s+Stmts\s+Miss\s+Cover(?:\s+Missing)?", re.IGNORECASE)

        if not header_pattern.search(log_content):
            return None

        # Pattern for module coverage lines
        # src/module_a.py             45      3    93%   12, 25-27
        # Note: Missing lines contain only digits, commas, spaces, and hyphens (ranges)
        # but must start with a digit (not a dash from separator lines)
        module_pattern = re.compile(
            r"^([\w/._-]+\.py)\s+(\d+)\s+(\d+)\s+(\d+)%(?:\s+(\d[\d,\s-]*))?\s*$",
            re.MULTILINE,
        )

        # Pattern for TOTAL line
        total_pattern = re.compile(r"^TOTAL\s+(\d+)\s+(\d+)\s+(\d+)%", re.MULTILINE)

        modules = []
        for match in module_pattern.finditer(log_content):
            module = {
                "name": match.group(1),
                "statements": int(match.group(2)),
                "missing": int(match.group(3)),
                "coverage": float(match.group(4)),
                "missing_lines": match.group(5).strip() if match.group(5) else "",
            }
            modules.append(module)

        # Extract total coverage
        total_match = total_pattern.search(log_content)
        if not total_match:
            return None

        coverage_data = {
            "total_statements": int(total_match.group(1)),
            "total_missing": int(total_match.group(2)),
            "total_coverage": float(total_match.group(3)),
            "modules": modules,
        }

        return coverage_data

    def parse_flake8_log(self, log_content: str) -> List[Dict]:
        """
        Parse flake8 output from CI logs.

        Extracts lint violations from flake8 output.

        Args:
            log_content: Raw flake8 log output

        Returns:
            List of violation dictionaries with keys:
            - file: File path
            - line: Line number
            - column: Column number
            - code: Violation code (e.g., "E501", "W291")
            - message: Violation message

        Examples:
            >>> parser = CILogParser()
            >>> violations = parser.parse_flake8_log(log_text)
            >>> violations[0]["code"]
            'E302'
        """
        if not log_content:
            return []

        violations = []

        # Pattern for flake8 violations:
        # ./src/module_a.py:15:1: E302 expected 2 blank lines, found 1
        violation_pattern = re.compile(r"^(.+?):(\d+):(\d+):\s+([A-Z]\d+)\s+(.+)$", re.MULTILINE)

        for match in violation_pattern.finditer(log_content):
            violation = {
                "file": match.group(1),
                "line": int(match.group(2)),
                "column": int(match.group(3)),
                "code": match.group(4),
                "message": match.group(5).strip(),
            }
            violations.append(violation)

        return violations

    def detect_failure_patterns(self, log_content: str) -> List[Dict]:
        """
        Detect common failure patterns in CI logs.

        Identifies recurring issues such as:
        - Timeout failures
        - Platform-specific failures
        - Setup/fixture failures
        - Import/dependency errors

        Args:
            log_content: Raw CI log output

        Returns:
            List of detected failure patterns with keys:
            - type: Pattern type ("timeout", "platform-specific", "setup", "dependency")
            - description: Human-readable description
            - occurrences: Number of times pattern appears
            - suggested_fix: Optional suggestion for fixing the issue

        Examples:
            >>> parser = CILogParser()
            >>> patterns = parser.parse_failure_patterns(log_text)
            >>> patterns[0]["type"]
            'timeout'
        """
        if not log_content:
            return []

        patterns = []

        # Detect timeout failures
        timeout_matches = re.findall(
            r"(?:Timeout|TIMEOUT|timed out).*?>?\s*(\d+(?:\.\d+)?)\s*s",
            log_content,
            re.IGNORECASE,
        )
        if timeout_matches:
            patterns.append(
                {
                    "type": "timeout",
                    "description": f"Test timeout detected ({len(timeout_matches)} occurrence(s))",
                    "occurrences": len(timeout_matches),
                    "suggested_fix": "Consider increasing timeout value or optimizing test performance",
                }
            )

        # Detect platform-specific skips
        platform_skips = re.findall(
            r"SKIPPED.*?(?:requires|Windows|Linux|Unix|macOS|Darwin)",
            log_content,
            re.IGNORECASE,
        )
        if platform_skips:
            patterns.append(
                {
                    "type": "platform-specific",
                    "description": f"Platform-specific test skips detected ({len(platform_skips)} occurrence(s))",
                    "occurrences": len(platform_skips),
                    "suggested_fix": "Use platform markers or run tests in appropriate environments",
                }
            )

        # Detect setup/fixture failures
        setup_errors = re.findall(
            r"ERROR at setup|fixture.*?failed|@pytest\.fixture",
            log_content,
            re.IGNORECASE,
        )
        if setup_errors:
            patterns.append(
                {
                    "type": "setup",
                    "description": f"Test setup/fixture failures detected ({len(setup_errors)} occurrence(s))",
                    "occurrences": len(setup_errors),
                    "suggested_fix": "Check fixture dependencies and initialization logic",
                }
            )

        # Detect import/dependency errors
        import_errors = re.findall(
            r"(?:ImportError|ModuleNotFoundError|No module named)",
            log_content,
            re.IGNORECASE,
        )
        if import_errors:
            patterns.append(
                {
                    "type": "dependency",
                    "description": f"Import/dependency errors detected ({len(import_errors)} occurrence(s))",
                    "occurrences": len(import_errors),
                    "suggested_fix": "Verify all dependencies are installed and available",
                }
            )

        return patterns
