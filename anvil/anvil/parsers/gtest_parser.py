"""
Parser for Google Test (gtest) JSON output.

This parser executes Google Test binaries and parses their JSON output
to extract test results, failures, and performance metrics.
"""

import json
import re
import subprocess
from typing import Dict, List, Optional, Tuple

from anvil.models.validator import Issue, ValidationResult


class GTestParser:
    """Parser for Google Test JSON output."""

    def parse_output(
        self, output: str, files: List[str], exit_code: Optional[int] = None
    ) -> ValidationResult:
        """
        Parse Google Test JSON output.

        Args:
            output: JSON output from gtest binary
            files: List of test binaries executed
            exit_code: Exit code from test execution

        Returns:
            ValidationResult with test failures and warnings
        """
        errors = []
        warnings = []

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            # Invalid JSON
            errors.append(
                Issue(
                    file_path=files[0] if files else "unknown",
                    line_number=0,
                    column_number=None,
                    message="Failed to parse gtest output: Invalid JSON",
                    rule_name="json-parse",
                    error_code="gtest-invalid-json",
                    severity="error",
                )
            )
            return ValidationResult(
                validator_name="gtest",
                passed=False,
                errors=errors,
                warnings=warnings,
                execution_time=0.0,
                files_checked=len(files),
            )

        # Extract summary
        total_tests = data.get("tests", 0)
        failures = data.get("failures", 0)
        data.get("disabled", 0)

        # Parse test suites
        testsuites = data.get("testsuites", [])
        for testsuite in testsuites:
            suite_name = testsuite.get("name", "UnknownSuite")
            tests = testsuite.get("testsuite", [])

            for test in tests:
                test_name = test.get("name", "UnknownTest")
                classname = test.get("classname", suite_name)
                status = test.get("status", "")
                test.get("result", "")

                # Check for disabled tests
                if status == "NOTRUN" or "DISABLED_" in test_name:
                    warnings.append(
                        Issue(
                            file_path=files[0] if files else "unknown",
                            line_number=0,
                            column_number=None,
                            message=f"Test disabled: {classname}.{test_name}",
                            rule_name="disabled-test",
                            error_code="gtest-disabled",
                            severity="warning",
                        )
                    )
                    continue

                # Check for failures
                test_failures = test.get("failures", [])
                if test_failures:
                    for failure in test_failures:
                        failure_msg = failure.get("failure", "Unknown failure")

                        # Try to extract file and line number
                        file_path = files[0] if files else "unknown"
                        line_number = 0

                        # Look for pattern like "file.cpp:123"
                        file_line_match = re.search(
                            r"([a-zA-Z0-9_./\\-]+\.(?:cpp|cc|h|hpp)):(\d+)",
                            failure_msg,
                        )
                        if file_line_match:
                            file_path = file_line_match.group(1)
                            line_number = int(file_line_match.group(2))

                        errors.append(
                            Issue(
                                file_path=file_path,
                                line_number=line_number,
                                column_number=None,
                                message=f"Test failed: {classname}.{test_name}\n{failure_msg}",
                                rule_name="test-failure",
                                error_code="gtest-fail",
                                severity="error",
                            )
                        )

        # If we have failures but no specific errors parsed, add summary
        if failures > 0 and len(errors) == 0:
            errors.append(
                Issue(
                    file_path=files[0] if files else "unknown",
                    line_number=0,
                    column_number=None,
                    message=f"{failures} test(s) failed out of {total_tests} total tests",
                    rule_name="test-summary",
                    error_code="gtest-summary",
                    severity="error",
                )
            )

        passed = failures == 0

        return ValidationResult(
            validator_name="gtest",
            passed=passed,
            errors=errors,
            warnings=warnings,
            execution_time=0.0,
            files_checked=len(files),
        )

    def build_command(self, files: List[str], options: Dict) -> List[str]:
        """
        Build gtest command with options.

        Args:
            files: List of test binary paths
            options: Configuration options

        Returns:
            Command as list of strings
        """
        if not files:
            raise ValueError("No test binaries specified")

        cmd = [files[0]]  # Test binary path

        # Output format (default to JSON)
        output_format = options.get("output_format", "json")
        if output_format == "json":
            cmd.append("--gtest_output=json:-")
        elif output_format == "xml":
            cmd.append("--gtest_output=xml:-")

        # Test filter
        if "filter" in options:
            cmd.append(f"--gtest_filter={options['filter']}")

        # Repeat tests
        if "repeat" in options:
            cmd.append(f"--gtest_repeat={options['repeat']}")

        # Shuffle tests
        if options.get("shuffle", False):
            cmd.append("--gtest_shuffle")

        # Break on failure
        if options.get("break_on_failure", False):
            cmd.append("--gtest_break_on_failure")

        # Run disabled tests
        if options.get("also_run_disabled_tests", False):
            cmd.append("--gtest_also_run_disabled_tests")

        return cmd

    def run(
        self, files: List[str], options: Dict, timeout: Optional[int] = None
    ) -> ValidationResult:
        """
        Run gtest binary and parse results.

        Args:
            files: List of test binary paths
            options: Configuration options
            timeout: Command timeout in seconds

        Returns:
            ValidationResult with test results

        Raises:
            FileNotFoundError: If test binary not found
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

        # For JSON output, parse stdout
        return self.parse_output(result.stdout, files, result.returncode)

    def get_version(self, files: List[str]) -> Optional[str]:
        """
        Get Google Test version from binary.

        Args:
            files: List of test binary paths

        Returns:
            Version string or None if not available
        """
        if not files:
            return None

        try:
            result = subprocess.run(
                [files[0], "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Look for version in output (stdout or stderr)
            output = result.stdout + result.stderr

            # Try to extract version
            # Format: "GoogleTest version 1.14.0" or similar
            version_match = re.search(r"GoogleTest version\s+(\d+\.\d+\.\d+)", output)
            if version_match:
                return version_match.group(1)

            # Alternative format
            version_match = re.search(r"version\s+(\d+\.\d+)", output)
            if version_match:
                return version_match.group(1)

            return None

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    def identify_slowest_tests(self, output: str, n: int = 10) -> List[Tuple[str, str]]:
        """
        Identify slowest tests from output.

        Args:
            output: JSON output from gtest
            n: Number of slowest tests to return

        Returns:
            List of (test_name, duration) tuples
        """
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return []

        tests_with_times = []

        testsuites = data.get("testsuites", [])
        for testsuite in testsuites:
            suite_name = testsuite.get("name", "")
            tests = testsuite.get("testsuite", [])

            for test in tests:
                test_name = test.get("name", "")
                classname = test.get("classname", suite_name)
                time = test.get("time", "0s")

                full_name = f"{classname}.{test_name}"
                tests_with_times.append((full_name, time))

        # Sort by duration (convert time string to float)
        def time_to_float(time_str: str) -> float:
            """Convert time string like '1.5s' to float."""
            try:
                return float(time_str.rstrip("s"))
            except (ValueError, AttributeError):
                return 0.0

        tests_with_times.sort(key=lambda x: time_to_float(x[1]), reverse=True)

        return tests_with_times[:n]

    def extract_total_duration(self, output: str) -> str:
        """
        Extract total test duration.

        Args:
            output: JSON output from gtest

        Returns:
            Total duration string
        """
        try:
            data = json.loads(output)
            return data.get("time", "0s")
        except json.JSONDecodeError:
            return "0s"

    def extract_summary(self, output: str) -> Dict[str, int]:
        """
        Extract test summary statistics.

        Args:
            output: JSON output from gtest

        Returns:
            Dictionary with total, passed, failures, disabled counts
        """
        try:
            data = json.loads(output)

            total = data.get("tests", 0)
            failures = data.get("failures", 0)
            disabled = data.get("disabled", 0)
            passed = total - failures - disabled

            return {
                "total": total,
                "passed": passed,
                "failures": failures,
                "disabled": disabled,
            }
        except json.JSONDecodeError:
            return {"total": 0, "passed": 0, "failures": 0, "disabled": 0}

    def calculate_pass_rate(self, output: str) -> float:
        """
        Calculate test pass rate.

        Args:
            output: JSON output from gtest

        Returns:
            Pass rate as percentage (0-100)
        """
        summary = self.extract_summary(output)

        tests_run = summary["total"] - summary["disabled"]
        if tests_run == 0:
            return 0.0

        passed = summary["passed"]
        return (passed / tests_run) * 100.0
