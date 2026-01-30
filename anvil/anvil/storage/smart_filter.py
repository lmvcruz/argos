"""
Smart filtering for test execution based on historical validation data.

This module provides intelligent filtering strategies to optimize test execution by:
- Skipping tests with consistently high success rates
- Prioritizing flaky tests that need investigation
- Prioritizing recently failing tests for quick feedback
- Always including new tests without history
"""

import fnmatch
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from anvil.storage.statistics_database import StatisticsDatabase


class SmartFilter:
    """
    Smart filter for optimizing test execution based on historical data.

    Uses statistical analysis of past test runs to make intelligent decisions about
    which tests to run, skip, or prioritize. This improves CI/CD efficiency while
    maintaining code quality.
    """

    def __init__(self, db: StatisticsDatabase):
        """
        Initialize smart filter with statistics database.

        Args:
            db: StatisticsDatabase instance for querying historical data
        """
        self.db = db

    def filter_tests(
        self,
        available_tests: List[Tuple[str, str]],
        enabled: bool = True,
        skip_threshold: float = 0.95,
        min_runs_required: int = 5,
        prioritize_flaky: bool = False,
        flaky_threshold_min: float = 0.3,
        flaky_threshold_max: float = 0.7,
        prioritize_recently_failing: bool = False,
        explicit_selection: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Filter tests based on historical data and configuration.

        Args:
            available_tests: List of (test_name, test_suite) tuples available to run
            enabled: Whether filtering is enabled (if False, runs all tests)
            skip_threshold: Skip tests with success rate above this threshold
            min_runs_required: Minimum runs needed for filtering decisions
            prioritize_flaky: Whether to prioritize flaky tests
            flaky_threshold_min: Minimum success rate for flaky test detection
            flaky_threshold_max: Maximum success rate for flaky test detection
            prioritize_recently_failing: Whether to prioritize recently failing tests
            explicit_selection: List of test name patterns that must run

        Returns:
            Dictionary containing:
                - tests_to_run: List of (test_name, test_suite) to execute
                - tests_skipped: List of dicts with skipped test details
                - prioritized_count: Number of tests prioritized
                - filtering_enabled: Whether filtering was active
                - insufficient_history: Whether history was insufficient
        """
        # If filtering disabled, run everything
        if not enabled:
            return {
                "tests_to_run": available_tests,
                "tests_skipped": [],
                "prioritized_count": 0,
                "filtering_enabled": False,
                "insufficient_history": False,
            }

        # Check if we have sufficient history
        all_runs = self.db.query_runs_by_date_range(start=datetime.min, end=datetime.max)

        if len(all_runs) < min_runs_required:
            # Insufficient history, run all tests
            return {
                "tests_to_run": available_tests,
                "tests_skipped": [],
                "prioritized_count": 0,
                "filtering_enabled": True,
                "insufficient_history": True,
            }

        # Build test history
        test_history = self._build_test_history(available_tests)

        # Separate tests into categories
        tests_to_run = []
        tests_to_skip = []
        prioritized_tests = []

        for test_name, test_suite in available_tests:
            key = (test_name, test_suite)

            # Check if explicitly selected
            if self._is_explicitly_selected(test_name, explicit_selection):
                tests_to_run.append(key)
                continue

            # Check if test has history
            if key not in test_history:
                # New test, always run
                tests_to_run.append(key)
                continue

            history = test_history[key]
            run_count = history["run_count"]
            success_rate = history["success_rate"]

            # Check if sufficient history for this test
            if run_count < min_runs_required:
                tests_to_run.append(key)
                continue

            # Check if should be prioritized as flaky
            if prioritize_flaky:
                if flaky_threshold_min <= success_rate < flaky_threshold_max:
                    prioritized_tests.append(key)
                    continue

            # Check if recently failing
            if prioritize_recently_failing and history.get("recently_failing", False):
                prioritized_tests.append(key)
                continue

            # Check if should be skipped (high success rate)
            if success_rate >= skip_threshold:
                tests_to_skip.append(
                    {
                        "test_name": test_name,
                        "test_suite": test_suite,
                        "success_rate": success_rate,
                        "run_count": run_count,
                    }
                )
            else:
                tests_to_run.append(key)

        # Prioritized tests go first
        final_test_list = prioritized_tests + tests_to_run

        return {
            "tests_to_run": final_test_list,
            "tests_skipped": tests_to_skip,
            "prioritized_count": len(prioritized_tests),
            "filtering_enabled": True,
            "insufficient_history": False,
        }

    def _build_test_history(
        self, available_tests: List[Tuple[str, str]]
    ) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """
        Build historical success rate data for available tests.

        Args:
            available_tests: List of (test_name, test_suite) tuples

        Returns:
            Dictionary mapping (test_name, test_suite) to history dict containing:
                - run_count: Number of times test was run
                - success_rate: Proportion of successful runs
                - recently_failing: Whether test failed in recent runs
        """
        # Get all runs
        all_runs = self.db.query_runs_by_date_range(start=datetime.min, end=datetime.max)

        if not all_runs:
            return {}

        # Build test case history
        test_cases_by_key: Dict[Tuple[str, str], List[bool]] = {}

        for run in all_runs:
            test_cases = self.db.query_test_cases_for_run(run.id)
            for tc in test_cases:
                key = (tc.test_name, tc.test_suite)
                if key not in test_cases_by_key:
                    test_cases_by_key[key] = []
                test_cases_by_key[key].append(tc.passed)

        # Calculate statistics
        test_history = {}
        for key, results in test_cases_by_key.items():
            if key in available_tests:
                passed_count = sum(1 for passed in results if passed)
                run_count = len(results)
                success_rate = passed_count / run_count if run_count > 0 else 0.0

                # Check if recently failing (last 2 runs)
                # Note: results are in DESC order (newest first) from database
                recently_failing = False
                if len(results) >= 2:
                    recent_results = results[:2]  # First 2 are most recent
                    recent_failures = sum(1 for passed in recent_results if not passed)
                    if recent_failures >= 1:
                        recently_failing = True

                test_history[key] = {
                    "run_count": run_count,
                    "success_rate": success_rate,
                    "recently_failing": recently_failing,
                }

        return test_history

    def _is_explicitly_selected(
        self, test_name: str, explicit_selection: Optional[List[str]]
    ) -> bool:
        """
        Check if test is explicitly selected via pattern matching.

        Args:
            test_name: Name of the test
            explicit_selection: List of test name patterns (supports wildcards)

        Returns:
            True if test matches any pattern, False otherwise
        """
        if not explicit_selection:
            return False

        for pattern in explicit_selection:
            if fnmatch.fnmatch(test_name, pattern):
                return True

        return False
