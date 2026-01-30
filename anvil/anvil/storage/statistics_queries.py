"""
Statistics query engine for analyzing historical validation data.

This module provides methods for querying and analyzing validation history
stored in the statistics database.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from anvil.storage.statistics_database import StatisticsDatabase


class StatisticsQueryEngine:
    """
    Query engine for analyzing historical validation data.

    Provides methods for calculating success rates, identifying flaky tests,
    finding problematic files, and analyzing trends over time.
    """

    def __init__(self, database: StatisticsDatabase):
        """
        Initialize the query engine.

        Args:
            database: Statistics database instance to query
        """
        self.db = database

    def get_test_success_rate(self, test_name: str, test_suite: str) -> float:
        """
        Calculate success rate for a specific test.

        Args:
            test_name: Name of the test
            test_suite: Test suite/module name

        Returns:
            Success rate as a float between 0.0 and 1.0
        """
        test_cases = self.db.query_test_history(test_name=test_name, limit=1000)

        # Filter by suite since query_test_history doesn't filter by suite
        test_cases = [tc for tc in test_cases if tc.test_suite == test_suite]

        if not test_cases:
            return 0.0

        passed_count = sum(1 for tc in test_cases if tc.passed)
        return passed_count / len(test_cases)

    def get_flaky_tests(
        self,
        min_success_rate: float = 0.3,
        max_success_rate: float = 0.9,
        min_runs: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Identify flaky tests based on success rate thresholds.

        Args:
            min_success_rate: Minimum success rate to consider (default 0.3)
            max_success_rate: Maximum success rate to consider (default 0.9)
            min_runs: Minimum number of runs required to classify as flaky (default 5)

        Returns:
            List of dictionaries with test_name, test_suite, success_rate, run_count
        """
        # Get all runs to query test cases from
        all_runs = self.db.query_runs_by_date_range(start=datetime.min, end=datetime.max)

        # Group test cases by (test_name, test_suite)
        test_groups: Dict[tuple, List] = {}
        for run in all_runs:
            test_cases = self.db.query_test_cases_for_run(run.id)
            for tc in test_cases:
                key = (tc.test_name, tc.test_suite)
                if key not in test_groups:
                    test_groups[key] = []
                test_groups[key].append(tc)

        flaky_tests = []
        for (test_name, test_suite), cases in test_groups.items():
            if len(cases) < min_runs:
                continue

            passed_count = sum(1 for tc in cases if tc.passed)
            success_rate = passed_count / len(cases)

            if min_success_rate <= success_rate <= max_success_rate:
                flaky_tests.append(
                    {
                        "test_name": test_name,
                        "test_suite": test_suite,
                        "success_rate": success_rate,
                        "run_count": len(cases),
                    }
                )

        return flaky_tests

    def get_file_error_frequency(self, file_path: str) -> float:
        """
        Calculate error frequency for a specific file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Error frequency as a float between 0.0 and 1.0
        """
        # Get all runs
        all_runs = self.db.query_runs_by_date_range(start=datetime.min, end=datetime.max)

        if not all_runs:
            return 0.0

        # Count how many runs had errors for this file
        error_count = 0
        for run in all_runs:
            file_validations = self.db.query_file_validations_for_run(run.id)
            for fv in file_validations:
                if fv.file_path == file_path and fv.error_count > 0:
                    error_count += 1
                    break  # Only count once per run

        return error_count / len(all_runs)

    def get_validator_trends(self, validator_name: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyze trends for a specific validator over time.

        Args:
            validator_name: Name of the validator to analyze
            days: Number of days to analyze (default 30)

        Returns:
            Dictionary with trend information: trend ("improving", "degrading", "stable"),
            error_count_change, average_errors, run_count
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # Get all validator results and filter by date
        validator_results = self.db.query_validator_history(
            validator_name=validator_name, limit=1000
        )

        # Filter by date manually since API doesn't support it
        filtered_results = []
        for vr in validator_results:
            run = self.db.get_validation_run(vr.run_id)
            if run and run.timestamp >= cutoff_date:
                filtered_results.append(vr)

        if not filtered_results:
            return {
                "trend": "unknown",
                "error_count_change": 0,
                "average_errors": 0.0,
                "run_count": 0,
            }

        # Already sorted by timestamp DESC in database query
        # Reverse to get chronological order
        sorted_results = list(reversed(filtered_results))

        # Split into first half (older) and second half (newer)
        mid_point = len(sorted_results) // 2
        first_half = sorted_results[:mid_point]
        second_half = sorted_results[mid_point:]

        avg_first = sum(vr.error_count for vr in first_half) / len(first_half)
        avg_second = sum(vr.error_count for vr in second_half) / len(second_half)

        error_count_change = avg_second - avg_first

        # Determine trend
        if error_count_change < -0.5:
            trend = "improving"
        elif error_count_change > 0.5:
            trend = "degrading"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "error_count_change": error_count_change,
            "average_errors": sum(vr.error_count for vr in sorted_results) / len(sorted_results),
            "run_count": len(sorted_results),
        }

    def get_problematic_files(self, threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        Identify files with high error frequency.

        Args:
            threshold: Minimum error frequency to consider problematic (default 0.6)

        Returns:
            List of dictionaries with file_path, error_frequency, total_runs
        """
        # Get all runs
        all_runs = self.db.query_runs_by_date_range(start=datetime.min, end=datetime.max)
        total_runs = len(all_runs)

        if total_runs == 0:
            return []

        # Track files and their error counts across all runs
        file_error_counts: Dict[str, int] = {}

        for run in all_runs:
            file_validations = self.db.query_file_validations_for_run(run.id)
            files_with_errors_in_run = set()

            for fv in file_validations:
                if fv.error_count > 0:
                    files_with_errors_in_run.add(fv.file_path)

            # Increment error count for each file that had errors in this run
            for file_path in files_with_errors_in_run:
                file_error_counts[file_path] = file_error_counts.get(file_path, 0) + 1

        problematic_files = []
        for file_path, error_count in file_error_counts.items():
            error_frequency = error_count / total_runs

            if error_frequency >= threshold:
                problematic_files.append(
                    {
                        "file_path": file_path,
                        "error_frequency": error_frequency,
                        "total_runs": total_runs,
                    }
                )

        return problematic_files

    def query_last_n_runs(self, n: int) -> List[Dict[str, Any]]:
        """
        Query the last N validation runs.

        Args:
            n: Number of runs to retrieve

        Returns:
            List of run dictionaries with run metadata
        """
        # Query all runs and take first N (already sorted newest first)
        runs = self.db.query_runs_by_date_range(start=datetime.min, end=datetime.max)
        runs = runs[:n]

        result = []
        for run in runs:
            result.append(
                {
                    "run_id": run.id,
                    "timestamp": run.timestamp,
                    "git_commit": run.git_commit,
                    "git_branch": run.git_branch,
                    "passed": run.passed,
                    "incremental": run.incremental,
                    "total_duration": run.duration_seconds,
                }
            )

        return result

    def query_runs_between_dates(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Query validation runs within a specific date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List of run dictionaries
        """
        runs = self.db.query_runs_by_date_range(start=start_date, end=end_date)

        result = []
        for run in runs:
            result.append(
                {
                    "run_id": run.id,
                    "timestamp": run.timestamp,
                    "git_commit": run.git_commit,
                    "git_branch": run.git_branch,
                    "passed": run.passed,
                    "incremental": run.incremental,
                    "total_duration": run.duration_seconds,
                }
            )

        return result

    def query_runs_for_branch(self, branch_name: str) -> List[Dict[str, Any]]:
        """
        Query validation runs for a specific git branch.

        Args:
            branch_name: Name of the git branch

        Returns:
            List of run dictionaries for the specified branch
        """
        branch_runs = self.db.query_runs_by_git_branch(branch=branch_name)

        result = []
        for run in branch_runs:
            result.append(
                {
                    "run_id": run.id,
                    "timestamp": run.timestamp,
                    "git_commit": run.git_commit,
                    "git_branch": run.git_branch,
                    "passed": run.passed,
                    "incremental": run.incremental,
                    "total_duration": run.duration_seconds,
                }
            )

        return result

    def get_aggregate_success_rate(self) -> float:
        """
        Calculate aggregate success rate across all tests.

        Returns:
            Overall success rate as a float between 0.0 and 1.0
        """
        # Get all runs
        all_runs = self.db.query_runs_by_date_range(start=datetime.min, end=datetime.max)

        if not all_runs:
            return 0.0

        total_tests = 0
        passed_tests = 0

        for run in all_runs:
            test_cases = self.db.query_test_cases_for_run(run.id)
            for tc in test_cases:
                total_tests += 1
                if tc.passed:
                    passed_tests += 1

        if total_tests == 0:
            return 0.0

        return passed_tests / total_tests

    def get_newly_failing_tests(
        self, recent_runs: int = 2, historical_runs: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Identify tests that were passing historically but are now failing.

        Args:
            recent_runs: Number of recent runs to check for failures (default 2)
            historical_runs: Number of historical runs to check for passes (default 5)

        Returns:
            List of newly failing test dictionaries
        """
        # Get all runs (sorted newest first)
        all_runs = self.db.query_runs_by_date_range(start=datetime.min, end=datetime.max)

        if len(all_runs) < recent_runs + historical_runs:
            return []

        recent_run_ids = [run.id for run in all_runs[:recent_runs]]
        historical_run_ids = [
            run.id for run in all_runs[recent_runs : recent_runs + historical_runs]
        ]

        # Get test cases from recent and historical runs
        recent_tests: Dict[tuple, List] = {}
        historical_tests: Dict[tuple, List] = {}

        for run_id in recent_run_ids:
            test_cases = self.db.query_test_cases_for_run(run_id)
            for tc in test_cases:
                key = (tc.test_name, tc.test_suite)
                if key not in recent_tests:
                    recent_tests[key] = []
                recent_tests[key].append(tc)

        for run_id in historical_run_ids:
            test_cases = self.db.query_test_cases_for_run(run_id)
            for tc in test_cases:
                key = (tc.test_name, tc.test_suite)
                if key not in historical_tests:
                    historical_tests[key] = []
                historical_tests[key].append(tc)

        # Find tests that are failing now but passed before
        newly_failing = []
        for key, recent_cases in recent_tests.items():
            if key not in historical_tests:
                continue

            historical_cases = historical_tests[key]

            # Check if test is failing in recent runs
            recent_pass_rate = sum(1 for tc in recent_cases if tc.passed) / len(recent_cases)
            # Check if test was passing in historical runs
            historical_pass_rate = sum(1 for tc in historical_cases if tc.passed) / len(
                historical_cases
            )

            if recent_pass_rate < 0.5 and historical_pass_rate >= 0.8:
                test_name, test_suite = key
                newly_failing.append(
                    {
                        "test_name": test_name,
                        "test_suite": test_suite,
                        "recent_pass_rate": recent_pass_rate,
                        "historical_pass_rate": historical_pass_rate,
                    }
                )

        return newly_failing

    def get_newly_passing_tests(
        self, recent_runs: int = 2, historical_runs: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Identify tests that were failing historically but are now passing.

        Args:
            recent_runs: Number of recent runs to check for passes (default 2)
            historical_runs: Number of historical runs to check for failures (default 5)

        Returns:
            List of newly passing test dictionaries
        """
        # Get all runs (sorted newest first)
        all_runs = self.db.query_runs_by_date_range(start=datetime.min, end=datetime.max)

        if len(all_runs) < recent_runs + historical_runs:
            return []

        recent_run_ids = [run.id for run in all_runs[:recent_runs]]
        historical_run_ids = [
            run.id for run in all_runs[recent_runs : recent_runs + historical_runs]
        ]

        # Get test cases from recent and historical runs
        recent_tests: Dict[tuple, List] = {}
        historical_tests: Dict[tuple, List] = {}

        for run_id in recent_run_ids:
            test_cases = self.db.query_test_cases_for_run(run_id)
            for tc in test_cases:
                key = (tc.test_name, tc.test_suite)
                if key not in recent_tests:
                    recent_tests[key] = []
                recent_tests[key].append(tc)

        for run_id in historical_run_ids:
            test_cases = self.db.query_test_cases_for_run(run_id)
            for tc in test_cases:
                key = (tc.test_name, tc.test_suite)
                if key not in historical_tests:
                    historical_tests[key] = []
                historical_tests[key].append(tc)

        # Find tests that are passing now but failed before
        newly_passing = []
        for key, recent_cases in recent_tests.items():
            if key not in historical_tests:
                continue

            historical_cases = historical_tests[key]

            # Check if test is passing in recent runs
            recent_pass_rate = sum(1 for tc in recent_cases if tc.passed) / len(recent_cases)
            # Check if test was failing in historical runs
            historical_pass_rate = sum(1 for tc in historical_cases if tc.passed) / len(
                historical_cases
            )

            if recent_pass_rate >= 0.8 and historical_pass_rate < 0.5:
                test_name, test_suite = key
                newly_passing.append(
                    {
                        "test_name": test_name,
                        "test_suite": test_suite,
                        "recent_pass_rate": recent_pass_rate,
                        "historical_pass_rate": historical_pass_rate,
                    }
                )

        return newly_passing
