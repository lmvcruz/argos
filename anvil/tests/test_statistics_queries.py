"""
Tests for StatisticsQueryEngine - analyzing historical validation data.

This module tests the query engine for analyzing historical validation data,
including success rates, flaky tests, problematic files, and trends.
"""

import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from anvil.models.validator import Issue, ValidationResult
from anvil.storage.statistics_database import StatisticsDatabase
from anvil.storage.statistics_persistence import StatisticsPersistence
from anvil.storage.statistics_queries import StatisticsQueryEngine


@pytest.fixture
def temp_db_and_engine():
    """
    Create temporary database with persistence and query engine.

    Yields:
        Tuple of (database, persistence, query_engine) for testing
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "stats.db"
        db = StatisticsDatabase(str(db_path))
        persistence = StatisticsPersistence(db)
        query_engine = StatisticsQueryEngine(db)
        try:
            yield (db, persistence, query_engine)
        finally:
            db.close()


class TestGetTestSuccessRate:
    """Test calculating success rate for specific tests."""

    def test_always_passing_test(self, temp_db_and_engine):
        """Test success rate calculation for a test that always passes."""
        db, persistence, query_engine = temp_db_and_engine

        # Create 5 runs with the same test always passing
        for i in range(5):
            results = [
                ValidationResult(
                    validator_name="pytest",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=1,
                    execution_time=1.0,
                    metadata={
                        "test_cases": [
                            {
                                "name": "test_example",
                                "suite": "tests.test_module",
                                "passed": True,
                                "skipped": False,
                                "duration": 0.5,
                            }
                        ]
                    },
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                total_duration=1.0,
            )

        success_rate = query_engine.get_test_success_rate(
            test_name="test_example", test_suite="tests.test_module"
        )

        assert success_rate == 1.0

    def test_always_failing_test(self, temp_db_and_engine):
        """Test success rate calculation for a test that always fails."""
        db, persistence, query_engine = temp_db_and_engine

        # Create 5 runs with the same test always failing
        for i in range(5):
            results = [
                ValidationResult(
                    validator_name="pytest",
                    passed=False,
                    errors=[
                        Issue(
                            file_path="tests/test_module.py",
                            line_number=10,
                            message="Test failed",
                            severity="error",
                        )
                    ],
                    warnings=[],
                    files_checked=1,
                    execution_time=1.0,
                    metadata={
                        "test_cases": [
                            {
                                "name": "test_failing",
                                "suite": "tests.test_module",
                                "passed": False,
                                "skipped": False,
                                "duration": 0.5,
                                "failure_message": "AssertionError: expected True",
                            }
                        ]
                    },
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                total_duration=1.0,
            )

        success_rate = query_engine.get_test_success_rate(
            test_name="test_failing", test_suite="tests.test_module"
        )

        assert success_rate == 0.0

    def test_flaky_test_three_of_five_pass_rate(self, temp_db_and_engine):
        """Test success rate calculation for a flaky test with 3/5 pass rate."""
        db, persistence, query_engine = temp_db_and_engine

        # Create 5 runs with the test passing 3 times, failing 2 times
        pass_pattern = [True, True, False, True, False]
        for i, should_pass in enumerate(pass_pattern):
            test_case = {
                "name": "test_flaky",
                "suite": "tests.test_module",
                "passed": should_pass,
                "skipped": False,
                "duration": 0.5,
            }
            if not should_pass:
                test_case["failure_message"] = "Random failure"

            results = [
                ValidationResult(
                    validator_name="pytest",
                    passed=should_pass,
                    errors=(
                        []
                        if should_pass
                        else [
                            Issue(
                                file_path="tests/test_module.py",
                                line_number=10,
                                message="Random failure",
                                severity="error",
                            )
                        ]
                    ),
                    warnings=[],
                    files_checked=1,
                    execution_time=1.0,
                    metadata={"test_cases": [test_case]},
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                total_duration=1.0,
            )

        success_rate = query_engine.get_test_success_rate(
            test_name="test_flaky", test_suite="tests.test_module"
        )

        assert success_rate == 0.6  # 3 out of 5


class TestGetFlakyTests:
    """Test identifying flaky tests based on thresholds."""

    def test_identify_flaky_with_threshold(self, temp_db_and_engine):
        """Test identifying flaky tests within success rate thresholds."""
        db, persistence, query_engine = temp_db_and_engine

        # Create a flaky test (passes 3/5 times = 60%)
        pass_pattern = [True, True, False, True, False]
        for i, should_pass in enumerate(pass_pattern):
            test_case = {
                "name": "test_flaky",
                "suite": "tests.test_module",
                "passed": should_pass,
                "skipped": False,
                "duration": 0.5,
            }
            if not should_pass:
                test_case["failure_message"] = "Flaky failure"

            results = [
                ValidationResult(
                    validator_name="pytest",
                    passed=should_pass,
                    errors=(
                        []
                        if should_pass
                        else [
                            Issue(
                                file_path="tests/test_module.py",
                                line_number=10,
                                message="Flaky failure",
                                severity="error",
                            )
                        ]
                    ),
                    warnings=[],
                    files_checked=1,
                    execution_time=1.0,
                    metadata={"test_cases": [test_case]},
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                total_duration=1.0,
            )

        # Also create a stable test (always passes)
        for i in range(5):
            results = [
                ValidationResult(
                    validator_name="pytest",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=1,
                    execution_time=1.0,
                    metadata={
                        "test_cases": [
                            {
                                "name": "test_stable",
                                "suite": "tests.test_module",
                                "passed": True,
                                "skipped": False,
                                "duration": 0.5,
                            }
                        ]
                    },
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"stable_commit{i}",
                git_branch="main",
                incremental=False,
                total_duration=1.0,
            )

        flaky_tests = query_engine.get_flaky_tests(
            min_success_rate=0.3, max_success_rate=0.9, min_runs=5
        )

        assert len(flaky_tests) == 1
        assert flaky_tests[0]["test_name"] == "test_flaky"
        assert flaky_tests[0]["test_suite"] == "tests.test_module"
        assert flaky_tests[0]["success_rate"] == 0.6
        assert flaky_tests[0]["run_count"] == 5

    def test_require_minimum_runs(self, temp_db_and_engine):
        """Test that flaky tests require minimum number of runs."""
        db, persistence, query_engine = temp_db_and_engine

        # Create a test with only 3 runs (below minimum of 5)
        pass_pattern = [True, False, True]
        for i, should_pass in enumerate(pass_pattern):
            test_case = {
                "name": "test_few_runs",
                "suite": "tests.test_module",
                "passed": should_pass,
                "skipped": False,
                "duration": 0.5,
            }

            results = [
                ValidationResult(
                    validator_name="pytest",
                    passed=should_pass,
                    errors=[],
                    warnings=[],
                    files_checked=1,
                    execution_time=1.0,
                    metadata={"test_cases": [test_case]},
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                total_duration=1.0,
            )

        flaky_tests = query_engine.get_flaky_tests(
            min_success_rate=0.3, max_success_rate=0.9, min_runs=5
        )

        # Should not identify as flaky due to insufficient runs
        assert len(flaky_tests) == 0


class TestGetFileErrorFrequency:
    """Test calculating error frequency for specific files."""

    def test_frequent_errors(self, temp_db_and_engine):
        """Test calculating error frequency for a file with frequent errors."""
        db, persistence, query_engine = temp_db_and_engine

        # Create 5 runs with the same file having errors in 4/5 runs
        error_pattern = [True, True, False, True, True]
        for i, has_error in enumerate(error_pattern):
            errors = []
            if has_error:
                errors.append(
                    Issue(
                        file_path="src/buggy_module.py",
                        line_number=42,
                        message="Syntax error",
                        severity="error",
                    )
                )

            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=not has_error,
                    errors=errors,
                    warnings=[],
                    files_checked=1,
                    execution_time=0.5,
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                total_duration=0.5,
            )

        error_frequency = query_engine.get_file_error_frequency("src/buggy_module.py")

        assert error_frequency == 0.8  # 4 out of 5

    def test_no_errors(self, temp_db_and_engine):
        """Test calculating error frequency for a file with no errors."""
        db, persistence, query_engine = temp_db_and_engine

        # Create 5 runs with no errors in the file
        for i in range(5):
            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=True,
                    errors=[],
                    warnings=[
                        Issue(
                            file_path="src/clean_module.py",
                            line_number=10,
                            message="Style warning",
                            severity="warning",
                        )
                    ],
                    files_checked=1,
                    execution_time=0.5,
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                total_duration=0.5,
            )

        error_frequency = query_engine.get_file_error_frequency("src/clean_module.py")

        assert error_frequency == 0.0


class TestGetValidatorTrends:
    """Test analyzing validator trends over time."""

    def test_improving_trend(self, temp_db_and_engine):
        """Test identifying improving trend in validator results."""
        db, persistence, query_engine = temp_db_and_engine

        # Create runs with decreasing error counts (improving)
        error_counts = [10, 9, 8, 5, 4, 3, 2, 1]
        base_time = datetime.now() - timedelta(days=7)

        for i, error_count in enumerate(error_counts):
            # Manually insert with specific timestamp
            from anvil.storage.statistics_database import ValidationRun, ValidatorRunRecord

            run = ValidationRun(
                timestamp=base_time + timedelta(days=i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=error_count == 0,
                duration_seconds=1.0,
            )
            run_id = db.insert_validation_run(run)

            validator_record = ValidatorRunRecord(
                run_id=run_id,
                validator_name="flake8",
                passed=error_count == 0,
                error_count=error_count,
                warning_count=0,
                files_checked=10,
                duration_seconds=1.0,
            )
            db.insert_validator_run_record(validator_record)

        trend_info = query_engine.get_validator_trends("flake8", days=10)

        assert trend_info["trend"] == "improving"
        assert trend_info["error_count_change"] < -0.5
        assert trend_info["run_count"] == 8

    def test_degrading_trend(self, temp_db_and_engine):
        """Test identifying degrading trend in validator results."""
        db, persistence, query_engine = temp_db_and_engine

        # Create runs with increasing error counts (degrading)
        error_counts = [1, 2, 3, 5, 6, 8, 10, 12]
        base_time = datetime.now() - timedelta(days=7)

        for i, error_count in enumerate(error_counts):
            # Manually insert with specific timestamp
            from anvil.storage.statistics_database import ValidationRun, ValidatorRunRecord

            run = ValidationRun(
                timestamp=base_time + timedelta(days=i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=False,
                duration_seconds=1.0,
            )
            run_id = db.insert_validation_run(run)

            validator_record = ValidatorRunRecord(
                run_id=run_id,
                validator_name="pylint",
                passed=False,
                error_count=error_count,
                warning_count=0,
                files_checked=10,
                duration_seconds=1.0,
            )
            db.insert_validator_run_record(validator_record)

        trend_info = query_engine.get_validator_trends("pylint", days=10)

        assert trend_info["trend"] == "degrading"
        assert trend_info["error_count_change"] > 0.5
        assert trend_info["run_count"] == 8


class TestGetProblematicFiles:
    """Test identifying files with high error frequency."""

    def test_files_above_threshold(self, temp_db_and_engine):
        """Test identifying problematic files above error threshold."""
        db, persistence, query_engine = temp_db_and_engine

        # Create runs with different files having different error frequencies
        # file1.py: 4/5 runs with errors (80%)
        # file2.py: 3/5 runs with errors (60%)
        # file3.py: 1/5 runs with errors (20%)
        error_patterns = {
            "src/file1.py": [True, True, False, True, True],
            "src/file2.py": [True, True, False, True, False],
            "src/file3.py": [True, False, False, False, False],
        }

        for i in range(5):
            errors = []
            for file_path, pattern in error_patterns.items():
                if pattern[i]:
                    errors.append(
                        Issue(
                            file_path=file_path,
                            line_number=1,
                            message=f"Error in {file_path}",
                            severity="error",
                        )
                    )

            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=len(errors) == 0,
                    errors=errors,
                    warnings=[],
                    files_checked=3,
                    execution_time=0.5,
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                total_duration=0.5,
            )

        problematic_files = query_engine.get_problematic_files(threshold=0.6)

        # Should find file1.py (80%) and file2.py (60%), not file3.py (20%)
        assert len(problematic_files) == 2
        assert problematic_files[0]["file_path"] == "src/file1.py"
        assert problematic_files[0]["error_frequency"] == 0.8
        assert problematic_files[1]["file_path"] == "src/file2.py"
        assert problematic_files[1]["error_frequency"] == 0.6


class TestQueryLastNRuns:
    """Test querying the last N validation runs."""

    def test_correct_number_of_runs(self, temp_db_and_engine):
        """Test querying returns correct number of runs."""
        db, persistence, query_engine = temp_db_and_engine

        # Create 10 runs
        for i in range(10):
            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=5,
                    execution_time=1.0,
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                total_duration=1.0,
            )

        last_5_runs = query_engine.query_last_n_runs(5)

        assert len(last_5_runs) == 5

    def test_most_recent_first(self, temp_db_and_engine):
        """Test querying returns most recent runs first."""
        db, persistence, query_engine = temp_db_and_engine

        # Create runs with identifiable commits
        for i in range(10):
            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=5,
                    execution_time=1.0,
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                total_duration=1.0,
            )
            # Small delay to ensure different timestamps
            time.sleep(0.01)

        last_3_runs = query_engine.query_last_n_runs(3)

        # Most recent should be commit9, then commit8, then commit7
        assert last_3_runs[0]["git_commit"] == "commit9"
        assert last_3_runs[1]["git_commit"] == "commit8"
        assert last_3_runs[2]["git_commit"] == "commit7"


class TestQueryRunsBetweenDates:
    """Test querying runs within a date range."""

    def test_returns_runs_in_date_range(self, temp_db_and_engine):
        """Test querying returns only runs within the specified date range."""
        db, persistence, query_engine = temp_db_and_engine

        # Create runs at different times
        base_time = datetime.now() - timedelta(days=10)

        for i in range(10):
            from anvil.storage.statistics_database import ValidationRun, ValidatorRunRecord

            run = ValidationRun(
                timestamp=base_time + timedelta(days=i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=True,
                duration_seconds=1.0,
            )
            run_id = db.insert_validation_run(run)

            validator_record = ValidatorRunRecord(
                run_id=run_id,
                validator_name="flake8",
                passed=True,
                error_count=0,
                warning_count=0,
                files_checked=5,
                duration_seconds=1.0,
            )
            db.insert_validator_run_record(validator_record)

        # Query runs from day 3 to day 7 (5 days inclusive)
        start_date = base_time + timedelta(days=3)
        end_date = base_time + timedelta(days=7)

        runs = query_engine.query_runs_between_dates(start_date, end_date)

        assert len(runs) == 5
        # Verify commits are in expected range
        commits = {run["git_commit"] for run in runs}
        expected_commits = {"commit3", "commit4", "commit5", "commit6", "commit7"}
        assert commits == expected_commits


class TestQueryRunsForBranch:
    """Test querying runs for a specific git branch."""

    def test_only_specific_branch(self, temp_db_and_engine):
        """Test querying returns only runs from the specified branch."""
        db, persistence, query_engine = temp_db_and_engine

        # Create runs on different branches
        branches = ["main", "main", "feature", "main", "feature", "hotfix"]
        for i, branch in enumerate(branches):
            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=5,
                    execution_time=1.0,
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"commit{i}",
                git_branch=branch,
                incremental=False,
                total_duration=1.0,
            )

        main_runs = query_engine.query_runs_for_branch("main")
        feature_runs = query_engine.query_runs_for_branch("feature")
        hotfix_runs = query_engine.query_runs_for_branch("hotfix")

        assert len(main_runs) == 3
        assert len(feature_runs) == 2
        assert len(hotfix_runs) == 1

        # Verify all returned runs are from correct branch
        for run in main_runs:
            assert run["git_branch"] == "main"
        for run in feature_runs:
            assert run["git_branch"] == "feature"


class TestGetAggregateSuccessRate:
    """Test calculating aggregate success rate across all tests."""

    def test_aggregate_success_rate_across_all_tests(self, temp_db_and_engine):
        """Test calculating aggregate success rate across all tests."""
        db, persistence, query_engine = temp_db_and_engine

        # Create runs with multiple tests, some passing, some failing
        # Total: 15 tests (10 passing, 5 failing) = 66.67% success rate
        test_scenarios = [
            # Run 1: 3 tests, all passing
            [
                {"name": "test1", "passed": True},
                {"name": "test2", "passed": True},
                {"name": "test3", "passed": True},
            ],
            # Run 2: 3 tests, 2 passing, 1 failing
            [
                {"name": "test1", "passed": True},
                {"name": "test2", "passed": False},
                {"name": "test3", "passed": True},
            ],
            # Run 3: 3 tests, 2 passing, 1 failing
            [
                {"name": "test1", "passed": True},
                {"name": "test2", "passed": True},
                {"name": "test3", "passed": False},
            ],
            # Run 4: 3 tests, 2 passing, 1 failing
            [
                {"name": "test1", "passed": True},
                {"name": "test2", "passed": False},
                {"name": "test3", "passed": True},
            ],
            # Run 5: 3 tests, 1 passing, 2 failing
            [
                {"name": "test1", "passed": True},
                {"name": "test2", "passed": False},
                {"name": "test3", "passed": False},
            ],
        ]

        for i, test_list in enumerate(test_scenarios):
            test_cases = [
                {
                    "name": test["name"],
                    "suite": "tests.test_module",
                    "passed": test["passed"],
                    "skipped": False,
                    "duration": 0.5,
                }
                for test in test_list
            ]

            results = [
                ValidationResult(
                    validator_name="pytest",
                    passed=all(t["passed"] for t in test_list),
                    errors=[],
                    warnings=[],
                    files_checked=1,
                    execution_time=1.5,
                    metadata={"test_cases": test_cases},
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                total_duration=1.5,
            )

        aggregate_rate = query_engine.get_aggregate_success_rate()

        # 10 passing out of 15 total = 0.6667
        assert abs(aggregate_rate - 0.6667) < 0.01


class TestGetNewlyFailingTests:
    """Test identifying tests that were passing but are now failing."""

    def test_were_passing_now_failing(self, temp_db_and_engine):
        """Test identifying tests that were passing historically but are now failing."""
        db, persistence, query_engine = temp_db_and_engine

        # Create historical runs where test passes
        for i in range(5):
            results = [
                ValidationResult(
                    validator_name="pytest",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=1,
                    execution_time=1.0,
                    metadata={
                        "test_cases": [
                            {
                                "name": "test_regression",
                                "suite": "tests.test_module",
                                "passed": True,
                                "skipped": False,
                                "duration": 0.5,
                            }
                        ]
                    },
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"old_commit{i}",
                git_branch="main",
                incremental=False,
                total_duration=1.0,
            )
            time.sleep(0.01)  # Ensure timestamp order

        # Create recent runs where test fails
        for i in range(2):
            results = [
                ValidationResult(
                    validator_name="pytest",
                    passed=False,
                    errors=[
                        Issue(
                            file_path="tests/test_module.py",
                            line_number=10,
                            message="Test failed",
                            severity="error",
                        )
                    ],
                    warnings=[],
                    files_checked=1,
                    execution_time=1.0,
                    metadata={
                        "test_cases": [
                            {
                                "name": "test_regression",
                                "suite": "tests.test_module",
                                "passed": False,
                                "skipped": False,
                                "duration": 0.5,
                                "failure_message": "AssertionError",
                            }
                        ]
                    },
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"new_commit{i}",
                git_branch="main",
                incremental=False,
                total_duration=1.0,
            )
            time.sleep(0.01)

        newly_failing = query_engine.get_newly_failing_tests(recent_runs=2, historical_runs=5)

        assert len(newly_failing) == 1
        assert newly_failing[0]["test_name"] == "test_regression"
        assert newly_failing[0]["test_suite"] == "tests.test_module"
        assert newly_failing[0]["recent_pass_rate"] == 0.0
        assert newly_failing[0]["historical_pass_rate"] == 1.0


class TestGetNewlyPassingTests:
    """Test identifying tests that were failing but are now passing."""

    def test_were_failing_now_passing(self, temp_db_and_engine):
        """Test identifying tests that were failing historically but are now passing."""
        db, persistence, query_engine = temp_db_and_engine

        # Create historical runs where test fails
        for i in range(5):
            results = [
                ValidationResult(
                    validator_name="pytest",
                    passed=False,
                    errors=[
                        Issue(
                            file_path="tests/test_module.py",
                            line_number=10,
                            message="Test failed",
                            severity="error",
                        )
                    ],
                    warnings=[],
                    files_checked=1,
                    execution_time=1.0,
                    metadata={
                        "test_cases": [
                            {
                                "name": "test_fixed",
                                "suite": "tests.test_module",
                                "passed": False,
                                "skipped": False,
                                "duration": 0.5,
                                "failure_message": "AssertionError",
                            }
                        ]
                    },
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"old_commit{i}",
                git_branch="main",
                incremental=False,
                total_duration=1.0,
            )
            time.sleep(0.01)

        # Create recent runs where test passes
        for i in range(2):
            results = [
                ValidationResult(
                    validator_name="pytest",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=1,
                    execution_time=1.0,
                    metadata={
                        "test_cases": [
                            {
                                "name": "test_fixed",
                                "suite": "tests.test_module",
                                "passed": True,
                                "skipped": False,
                                "duration": 0.5,
                            }
                        ]
                    },
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"new_commit{i}",
                git_branch="main",
                incremental=False,
                total_duration=1.0,
            )
            time.sleep(0.01)

        newly_passing = query_engine.get_newly_passing_tests(recent_runs=2, historical_runs=5)

        assert len(newly_passing) == 1
        assert newly_passing[0]["test_name"] == "test_fixed"
        assert newly_passing[0]["test_suite"] == "tests.test_module"
        assert newly_passing[0]["recent_pass_rate"] == 1.0
        assert newly_passing[0]["historical_pass_rate"] == 0.0


class TestPerformance:
    """Test query performance with large datasets."""

    def test_handle_100_runs_with_10_tests_each_under_1_second(self, temp_db_and_engine):
        """Test handling 100 runs with 10 tests each (1000 records) in < 1 second."""
        db, persistence, query_engine = temp_db_and_engine

        # Create 100 runs with 10 tests each (1000 test case records)
        start_time = time.time()

        for run_num in range(100):
            test_cases = []
            for test_num in range(10):
                # Vary pass/fail to make data realistic
                passed = (run_num + test_num) % 3 != 0  # ~67% pass rate

                test_cases.append(
                    {
                        "name": f"test_{test_num}",
                        "suite": "tests.test_module",
                        "passed": passed,
                        "skipped": False,
                        "duration": 0.1,
                    }
                )

            results = [
                ValidationResult(
                    validator_name="pytest",
                    passed=all(tc["passed"] for tc in test_cases),
                    errors=[],
                    warnings=[],
                    files_checked=10,
                    execution_time=1.0,
                    metadata={"test_cases": test_cases},
                )
            ]
            persistence.save_validation_run(
                results=results,
                git_commit=f"commit{run_num}",
                git_branch="main",
                incremental=False,
                total_duration=1.0,
            )

        insertion_time = time.time() - start_time

        # Now test query performance
        query_start = time.time()

        # Run various queries
        aggregate_rate = query_engine.get_aggregate_success_rate()
        last_10_runs = query_engine.query_last_n_runs(10)
        flaky_tests = query_engine.get_flaky_tests(min_runs=10)
        success_rate = query_engine.get_test_success_rate("test_0", "tests.test_module")

        query_time = time.time() - query_start

        # Verify queries completed successfully
        assert aggregate_rate > 0.0
        assert len(last_10_runs) == 10
        assert isinstance(flaky_tests, list)
        assert success_rate >= 0.0

        # Performance assertion: queries should complete in < 1 second
        assert query_time < 1.0, f"Queries took {query_time:.2f}s, expected < 1.0s"

        # Optional: print performance metrics for reference
        print("\nPerformance metrics:")
        print(f"  Insertion time: {insertion_time:.2f}s for 100 runs (1000 test records)")
        print(f"  Query time: {query_time:.2f}s for 4 complex queries")
