#!/usr/bin/env python3
"""
Parse test failure output from pytest logs.

This script parses pytest output (from file or stdin) and extracts
a clean summary of failed tests.

Usage:
    # From a file
    python scripts/parse-test-failures.py pytest-output.txt

    # From stdin (pipe from pytest)
    pytest --tb=short 2>&1 | python scripts/parse-test-failures.py

    # With detailed output
    python scripts/parse-test-failures.py --detailed pytest-output.txt
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional


class TestFailureParser:
    """Parse pytest failure output."""

    def __init__(self, content: str):
        """
        Initialize parser with test output.

        Args:
            content: Pytest output text
        """
        self.content = content

    def extract_failed_tests(self) -> List[Dict[str, str]]:
        """
        Extract failed test information.

        Returns:
            List of dictionaries with test failure info
        """
        failures = []

        # Pattern for FAILED lines
        failed_pattern = re.compile(
            r"^(FAILED|ERROR)\s+([\w/:.]+::\w+(?:::\w+)*)\s*-?\s*(.*)$", re.MULTILINE
        )

        for match in failed_pattern.finditer(self.content):
            failure_type = match.group(1)
            test_name = match.group(2)
            error_msg = match.group(3).strip()

            failures.append(
                {"type": failure_type, "test": test_name, "error": error_msg}
            )

        return failures

    def extract_failure_details(self, test_name: str) -> Optional[str]:
        """
        Extract detailed failure information for a specific test.

        Args:
            test_name: Name of the test to extract details for

        Returns:
            Detailed failure information or None
        """
        # Look for the detailed failure section
        # Pattern: _____ TestClass::test_name _____
        escaped_name = re.escape(test_name)
        pattern = re.compile(
            rf"_{10,}\s+{escaped_name}\s+_{10,}(.*?)(?=_{10,}|\Z)", re.DOTALL
        )

        match = pattern.search(self.content)
        if match:
            details = match.group(1).strip()
            # Clean up ANSI escape codes
            details = re.sub(r"\x1b\[[0-9;]*m", "", details)
            return details

        return None

    def extract_summary(self) -> Optional[Dict[str, int]]:
        """
        Extract test summary (passed/failed/skipped counts).

        Returns:
            Dictionary with test counts or None
        """
        # Pattern: === 5 failed, 10 passed, 2 skipped in 5.23s ===
        summary_pattern = re.compile(
            r"=+\s*"
            r"(?:(\d+)\s+failed[,\s]*)?"
            r"(?:(\d+)\s+passed[,\s]*)?"
            r"(?:(\d+)\s+skipped[,\s]*)?"
            r"(?:(\d+)\s+error[,\s]*)?"
            r".*in\s+([\d.]+)s",
            re.IGNORECASE,
        )

        match = summary_pattern.search(self.content)
        if match:
            return {
                "failed": int(match.group(1) or 0),
                "passed": int(match.group(2) or 0),
                "skipped": int(match.group(3) or 0),
                "errors": int(match.group(4) or 0),
                "duration": float(match.group(5)),
            }

        return None

    def extract_short_errors(self) -> List[Dict[str, str]]:
        """
        Extract short test error messages from traceback.

        Returns:
            List of test errors with minimal context
        """
        errors = []

        # Pattern for assertion errors
        assertion_pattern = re.compile(
            r"([\w/:.]+::\w+(?:::\w+)*)[^\n]*\n.*?(AssertionError|Error|Exception): (.+)",
            re.MULTILINE,
        )

        for match in assertion_pattern.finditer(self.content):
            test_name = match.group(1)
            error_type = match.group(2)
            error_msg = match.group(3).strip()

            errors.append(
                {"test": test_name, "error_type": error_type, "message": error_msg}
            )

        return errors


def print_failure_summary(failures: List[Dict], detailed: bool = False) -> None:
    """
    Print a summary of test failures.

    Args:
        failures: List of failure dictionaries
        detailed: Whether to include detailed context
    """
    if not failures:
        print("✓ No test failures found")
        return

    print(f"\n{'='*80}")
    print(f"❌ Found {len(failures)} test failure(s)")
    print(f"{'='*80}\n")

    for i, failure in enumerate(failures, 1):
        failure_type = failure.get("type", "FAILED")
        test_name = failure["test"]
        error_msg = failure.get("error", "")

        print(f"{i}. [{failure_type}] {test_name}")

        if error_msg:
            print(f"   Error: {error_msg}")

        if detailed and "details" in failure:
            print(f"\n   Details:")
            print("   " + "\n   ".join(failure["details"].split("\n")[:20]))
            print()
        else:
            print()


def print_test_summary(summary: Optional[Dict]) -> None:
    """
    Print test execution summary.

    Args:
        summary: Dictionary with test counts
    """
    if not summary:
        return

    print(f"{'='*80}")
    print("Test Summary:")
    print(f"  Passed:  {summary['passed']}")
    print(f"  Failed:  {summary['failed']}")
    print(f"  Skipped: {summary['skipped']}")
    print(f"  Errors:  {summary['errors']}")
    print(f"  Duration: {summary['duration']:.2f}s")
    print(f"{'='*80}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Parse pytest failure output and extract clean summaries"
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        help="File containing pytest output (or read from stdin)",
    )
    parser.add_argument(
        "-d",
        "--detailed",
        action="store_true",
        help="Show detailed failure context",
    )
    parser.add_argument(
        "-s",
        "--summary-only",
        action="store_true",
        help="Show only summary statistics",
    )

    args = parser.parse_args()

    # Read input
    if args.file:
        if not args.file.exists():
            print(f"Error: File not found: {args.file}")
            return 1
        content = args.file.read_text(encoding="utf-8", errors="ignore")
    else:
        # Read from stdin
        if sys.stdin.isatty():
            print("Error: No input provided. Pipe pytest output or provide a file.")
            print("Usage: pytest 2>&1 | python scripts/parse-test-failures.py")
            return 1
        content = sys.stdin.read()

    # Parse content
    parser_obj = TestFailureParser(content)

    # Extract summary
    summary = parser_obj.extract_summary()

    if args.summary_only:
        print_test_summary(summary)
        return 0

    # Extract failures
    failures = parser_obj.extract_failed_tests()

    # Add details if requested
    if args.detailed:
        for failure in failures:
            details = parser_obj.extract_failure_details(failure["test"])
            if details:
                failure["details"] = details

    # Print results
    print_test_summary(summary)
    print_failure_summary(failures, args.detailed)

    # Return exit code based on failures
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
