"""
Test result logging and output formatting.

This module handles formatting and displaying test results in various formats.
"""

import json
from typing import Any, Dict, List

from verdict.runner import TestResult


class TestLogger:
    """
    Formats and outputs test results.

    Supports console output (plain text and colored) and JSON output.
    """

    def __init__(self, use_color: bool = True):
        """
        Initialize test logger.

        Args:
            use_color: Whether to use colored output (default: True)
        """
        self.use_color = use_color

    def log_console(self, results: List[TestResult]) -> None:
        """
        Output results to console in human-readable format.

        Args:
            results: List of test results
        """
        # Print summary header
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        print("\n" + "=" * 70)
        print(f"TEST RESULTS: {passed} passed, {failed} failed, {total} total")
        print("=" * 70 + "\n")

        # Group results by suite
        suites: Dict[str, List[TestResult]] = {}
        for result in results:
            suite_name = result.suite_name
            if suite_name not in suites:
                suites[suite_name] = []
            suites[suite_name].append(result)

        # Print results by suite
        for suite_name, suite_results in suites.items():
            self._print_suite_results(suite_name, suite_results)

        # Print overall summary
        print("\n" + "=" * 70)
        if failed == 0:
            self._print_colored("✓ ALL TESTS PASSED", "green")
        else:
            self._print_colored(f"✗ {failed} TEST(S) FAILED", "red")
        print("=" * 70 + "\n")

    def log_json(self, results: List[TestResult]) -> str:
        """
        Output results as JSON string.

        Args:
            results: List of test results

        Returns:
            JSON-formatted string
        """
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        output = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
            },
            "results": [r.to_dict() for r in results],
        }

        return json.dumps(output, indent=2)

    def _print_suite_results(self, suite_name: str, results: List[TestResult]) -> None:
        """
        Print results for a single test suite.

        Args:
            suite_name: Name of the test suite
            results: List of test results for this suite
        """
        print(f"\n{suite_name}")
        print("-" * 70)

        for result in results:
            if result.passed:
                self._print_colored(f"  ✓ {result.test_name}", "green")
            else:
                self._print_colored(f"  ✗ {result.test_name}", "red")

                # Print error or differences
                if result.error:
                    print(f"    Error: {result.error}")
                elif result.differences:
                    print("    Differences:")
                    for diff in result.differences:
                        print(f"      - {diff}")

    def _print_colored(self, text: str, color: str) -> None:
        """
        Print colored text to console.

        Args:
            text: Text to print
            color: Color name (green, red, yellow)
        """
        if not self.use_color:
            print(text)
            return

        colors = {
            "green": "\033[92m",
            "red": "\033[91m",
            "yellow": "\033[93m",
            "reset": "\033[0m",
        }

        color_code = colors.get(color, "")
        reset_code = colors["reset"]
        print(f"{color_code}{text}{reset_code}")
