"""
Comprehensive tests for smart filtering based on historical validation data.

Tests cover filtering optimization strategies including skipping high-success tests,
prioritizing flaky tests, and handling edge cases with insufficient historical data.
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from anvil.storage.smart_filter import SmartFilter
from anvil.storage.statistics_database import (
    StatisticsDatabase,
    TestCaseRecord,
    ValidationRun,
)
from anvil.storage.statistics_persistence import StatisticsPersistence


@pytest.fixture
def temp_db_and_filter():
    """Create temporary database and smart filter for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "stats.db"
        db = StatisticsDatabase(db_path)
        persistence = StatisticsPersistence(db)
        smart_filter = SmartFilter(db)
        try:
            yield (db, persistence, smart_filter)
        finally:
            db.close()


class TestSkipHighSuccessTests:
    """Test filtering to skip tests with high success rates."""

    def test_skip_tests_above_threshold(self, temp_db_and_filter):
        """Test that tests with success rate above threshold are skipped."""
        db, persistence, smart_filter = temp_db_and_filter

        # Create 10 runs with consistent test results
        for i in range(10):
            run = ValidationRun(
                timestamp=datetime.now() - timedelta(days=10 - i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=True,
                duration_seconds=10.0,
            )
            run_id = db.insert_validation_run(run)

            # test_always_passing: 10/10 pass (100%)
            db.insert_test_case_record(
                TestCaseRecord(
                    run_id=run_id,
                    test_name="test_always_passing",
                    test_suite="TestSuite",
                    passed=True,
                    duration_seconds=0.1,
                    failure_message=None,
                    skipped=False,
                )
            )

            # test_sometimes_failing: 5/10 pass (50%)
            db.insert_test_case_record(
                TestCaseRecord(
                    run_id=run_id,
                    test_name="test_sometimes_failing",
                    test_suite="TestSuite",
                    passed=i < 5,
                    duration_seconds=0.1,
                    failure_message="Failed" if i >= 5 else None,
                    skipped=False,
                )
            )

        # Filter with 90% threshold
        result = smart_filter.filter_tests(
            available_tests=[
                ("test_always_passing", "TestSuite"),
                ("test_sometimes_failing", "TestSuite"),
            ],
            skip_threshold=0.9,
        )

        # test_always_passing should be skipped (100% > 90%)
        assert len(result["tests_to_run"]) == 1
        assert result["tests_to_run"][0] == ("test_sometimes_failing", "TestSuite")
        assert len(result["tests_skipped"]) == 1
        assert result["tests_skipped"][0]["test_name"] == "test_always_passing"
        assert result["tests_skipped"][0]["success_rate"] == 1.0

    def test_all_tests_run_when_below_threshold(self, temp_db_and_filter):
        """Test that all tests run when none exceed threshold."""
        db, persistence, smart_filter = temp_db_and_filter

        # Create runs with moderate success rates
        for i in range(10):
            run = ValidationRun(
                timestamp=datetime.now() - timedelta(days=10 - i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=False,
                duration_seconds=10.0,
            )
            run_id = db.insert_validation_run(run)

            # test_moderate: 8/10 pass (80%)
            db.insert_test_case_record(
                TestCaseRecord(
                    run_id=run_id,
                    test_name="test_moderate",
                    test_suite="TestSuite",
                    passed=i < 8,
                    duration_seconds=0.1,
                    failure_message=None if i < 8 else "Failed",
                    skipped=False,
                )
            )

        result = smart_filter.filter_tests(
            available_tests=[("test_moderate", "TestSuite")],
            skip_threshold=0.9,
        )

        # Should run because 80% < 90%
        assert len(result["tests_to_run"]) == 1
        assert len(result["tests_skipped"]) == 0


class TestPrioritizeFlakyTests:
    """Test prioritization of flaky tests."""

    def test_flaky_tests_run_first(self, temp_db_and_filter):
        """Test that flaky tests are prioritized to run first."""
        db, persistence, smart_filter = temp_db_and_filter

        # Create 10 runs with various test patterns
        for i in range(10):
            run = ValidationRun(
                timestamp=datetime.now() - timedelta(days=10 - i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=False,
                duration_seconds=10.0,
            )
            run_id = db.insert_validation_run(run)

            # test_flaky: alternating pass/fail (50%)
            db.insert_test_case_record(
                TestCaseRecord(
                    run_id=run_id,
                    test_name="test_flaky",
                    test_suite="TestSuite",
                    passed=i % 2 == 0,
                    duration_seconds=0.1,
                    failure_message=None if i % 2 == 0 else "Flaky",
                    skipped=False,
                )
            )

            # test_stable: 7/10 pass (70%)
            db.insert_test_case_record(
                TestCaseRecord(
                    run_id=run_id,
                    test_name="test_stable",
                    test_suite="TestSuite",
                    passed=i < 7,
                    duration_seconds=0.1,
                    failure_message=None if i < 7 else "Failed",
                    skipped=False,
                )
            )

        result = smart_filter.filter_tests(
            available_tests=[
                ("test_stable", "TestSuite"),
                ("test_flaky", "TestSuite"),
            ],
            prioritize_flaky=True,
            flaky_threshold_min=0.3,
            flaky_threshold_max=0.7,
        )

        # Both should run, but flaky test first
        assert len(result["tests_to_run"]) == 2
        assert result["tests_to_run"][0] == ("test_flaky", "TestSuite")
        assert result["tests_to_run"][1] == ("test_stable", "TestSuite")
        assert result["prioritized_count"] == 1


class TestPrioritizeRecentlyFailingTests:
    """Test prioritization of recently failing tests."""

    def test_recently_failing_tests_prioritized(self, temp_db_and_filter):
        """Test that recently failing tests run first."""
        db, persistence, smart_filter = temp_db_and_filter

        base_time = datetime.now()

        # Create historical runs (older)
        for i in range(5):
            run = ValidationRun(
                timestamp=base_time - timedelta(days=10 + i),
                git_commit=f"old_commit{i}",
                git_branch="main",
                incremental=False,
                passed=True,
                duration_seconds=10.0,
            )
            run_id = db.insert_validation_run(run)

            # test_recently_failing: was passing in history
            db.insert_test_case_record(
                TestCaseRecord(
                    run_id=run_id,
                    test_name="test_recently_failing",
                    test_suite="TestSuite",
                    passed=True,
                    duration_seconds=0.1,
                    failure_message=None,
                    skipped=False,
                )
            )

        # Create recent runs (newer)
        for i in range(2):
            run = ValidationRun(
                timestamp=base_time - timedelta(days=i),
                git_commit=f"recent_commit{i}",
                git_branch="main",
                incremental=False,
                passed=False,
                duration_seconds=10.0,
            )
            run_id = db.insert_validation_run(run)

            # test_recently_failing: now failing
            db.insert_test_case_record(
                TestCaseRecord(
                    run_id=run_id,
                    test_name="test_recently_failing",
                    test_suite="TestSuite",
                    passed=False,
                    duration_seconds=0.1,
                    failure_message="Recent failure",
                    skipped=False,
                )
            )

        result = smart_filter.filter_tests(
            available_tests=[("test_recently_failing", "TestSuite")],
            prioritize_recently_failing=True,
        )

        # Should be prioritized
        assert len(result["tests_to_run"]) == 1
        assert result["prioritized_count"] == 1


class TestIncludeNewTests:
    """Test inclusion of new tests never seen before."""

    def test_new_tests_always_included(self, temp_db_and_filter):
        """Test that new tests are always included in run."""
        db, persistence, smart_filter = temp_db_and_filter

        # Create history for existing test only
        for i in range(10):
            run = ValidationRun(
                timestamp=datetime.now() - timedelta(days=10 - i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=True,
                duration_seconds=10.0,
            )
            run_id = db.insert_validation_run(run)

            db.insert_test_case_record(
                TestCaseRecord(
                    run_id=run_id,
                    test_name="test_existing",
                    test_suite="TestSuite",
                    passed=True,
                    duration_seconds=0.1,
                    failure_message=None,
                    skipped=False,
                )
            )

        result = smart_filter.filter_tests(
            available_tests=[
                ("test_existing", "TestSuite"),
                ("test_new", "TestSuite"),
            ],
            skip_threshold=0.9,
        )

        # New test should always run, existing might be skipped
        tests_to_run = result["tests_to_run"]
        assert ("test_new", "TestSuite") in tests_to_run
        # test_existing has 100% success, should be skipped
        assert ("test_existing", "TestSuite") not in tests_to_run


class TestInsufficientHistory:
    """Test handling of insufficient historical data."""

    def test_all_tests_run_with_insufficient_history(self, temp_db_and_filter):
        """Test that all tests run when history is insufficient."""
        db, persistence, smart_filter = temp_db_and_filter

        # Create only 2 runs (less than minimum required)
        for i in range(2):
            run = ValidationRun(
                timestamp=datetime.now() - timedelta(days=2 - i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=True,
                duration_seconds=10.0,
            )
            run_id = db.insert_validation_run(run)

            db.insert_test_case_record(
                TestCaseRecord(
                    run_id=run_id,
                    test_name="test_with_little_history",
                    test_suite="TestSuite",
                    passed=True,
                    duration_seconds=0.1,
                    failure_message=None,
                    skipped=False,
                )
            )

        result = smart_filter.filter_tests(
            available_tests=[("test_with_little_history", "TestSuite")],
            skip_threshold=0.9,
            min_runs_required=5,
        )

        # Should run all tests due to insufficient history
        assert len(result["tests_to_run"]) == 1
        assert result["insufficient_history"] is True

    def test_empty_database_runs_all_tests(self, temp_db_and_filter):
        """Test that all tests run when database is empty."""
        db, persistence, smart_filter = temp_db_and_filter

        result = smart_filter.filter_tests(
            available_tests=[
                ("test_any", "TestSuite"),
                ("test_another", "TestSuite"),
            ],
            skip_threshold=0.9,
        )

        # All tests should run
        assert len(result["tests_to_run"]) == 2
        assert result["insufficient_history"] is True


class TestFilteringDisabled:
    """Test disabled filtering mode."""

    def test_all_tests_run_when_disabled(self, temp_db_and_filter):
        """Test that all tests run when filtering is disabled."""
        db, persistence, smart_filter = temp_db_and_filter

        # Create history with perfect success
        for i in range(10):
            run = ValidationRun(
                timestamp=datetime.now() - timedelta(days=10 - i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=True,
                duration_seconds=10.0,
            )
            run_id = db.insert_validation_run(run)

            db.insert_test_case_record(
                TestCaseRecord(
                    run_id=run_id,
                    test_name="test_perfect",
                    test_suite="TestSuite",
                    passed=True,
                    duration_seconds=0.1,
                    failure_message=None,
                    skipped=False,
                )
            )

        result = smart_filter.filter_tests(
            available_tests=[("test_perfect", "TestSuite")],
            enabled=False,
        )

        # Should run all tests even though filtering would skip them
        assert len(result["tests_to_run"]) == 1
        assert len(result["tests_skipped"]) == 0
        assert result["filtering_enabled"] is False


class TestFilteringConfiguration:
    """Test smart filter configuration options."""

    def test_custom_skip_threshold(self, temp_db_and_filter):
        """Test filtering with custom skip threshold."""
        db, persistence, smart_filter = temp_db_and_filter

        # Create runs with 80% success rate
        for i in range(10):
            run = ValidationRun(
                timestamp=datetime.now() - timedelta(days=10 - i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=i < 8,
                duration_seconds=10.0,
            )
            run_id = db.insert_validation_run(run)

            db.insert_test_case_record(
                TestCaseRecord(
                    run_id=run_id,
                    test_name="test_80_percent",
                    test_suite="TestSuite",
                    passed=i < 8,
                    duration_seconds=0.1,
                    failure_message=None if i < 8 else "Failed",
                    skipped=False,
                )
            )

        # With 70% threshold, should skip
        result = smart_filter.filter_tests(
            available_tests=[("test_80_percent", "TestSuite")],
            skip_threshold=0.7,
        )
        assert len(result["tests_skipped"]) == 1

        # With 90% threshold, should run
        result = smart_filter.filter_tests(
            available_tests=[("test_80_percent", "TestSuite")],
            skip_threshold=0.9,
        )
        assert len(result["tests_to_run"]) == 1

    def test_custom_minimum_runs(self, temp_db_and_filter):
        """Test filtering with custom minimum runs requirement."""
        db, persistence, smart_filter = temp_db_and_filter

        # Create exactly 3 runs
        for i in range(3):
            run = ValidationRun(
                timestamp=datetime.now() - timedelta(days=3 - i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=True,
                duration_seconds=10.0,
            )
            run_id = db.insert_validation_run(run)

            db.insert_test_case_record(
                TestCaseRecord(
                    run_id=run_id,
                    test_name="test_few_runs",
                    test_suite="TestSuite",
                    passed=True,
                    duration_seconds=0.1,
                    failure_message=None,
                    skipped=False,
                )
            )

        # With min_runs_required=2, should have sufficient history
        result = smart_filter.filter_tests(
            available_tests=[("test_few_runs", "TestSuite")],
            skip_threshold=0.9,
            min_runs_required=2,
        )
        assert result["insufficient_history"] is False
        assert len(result["tests_skipped"]) == 1  # 100% success

        # With min_runs_required=5, insufficient history
        result = smart_filter.filter_tests(
            available_tests=[("test_few_runs", "TestSuite")],
            skip_threshold=0.9,
            min_runs_required=5,
        )
        assert result["insufficient_history"] is True
        assert len(result["tests_to_run"]) == 1


class TestFilteringReport:
    """Test filtering report generation."""

    def test_report_includes_skipped_tests(self, temp_db_and_filter):
        """Test that filtering report includes details of skipped tests."""
        db, persistence, smart_filter = temp_db_and_filter

        # Create perfect test history
        for i in range(10):
            run = ValidationRun(
                timestamp=datetime.now() - timedelta(days=10 - i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=True,
                duration_seconds=10.0,
            )
            run_id = db.insert_validation_run(run)

            db.insert_test_case_record(
                TestCaseRecord(
                    run_id=run_id,
                    test_name="test_skip_me",
                    test_suite="TestSuite",
                    passed=True,
                    duration_seconds=0.1,
                    failure_message=None,
                    skipped=False,
                )
            )

        result = smart_filter.filter_tests(
            available_tests=[("test_skip_me", "TestSuite")],
            skip_threshold=0.9,
        )

        # Check report fields
        assert "tests_to_run" in result
        assert "tests_skipped" in result
        assert "prioritized_count" in result
        assert "filtering_enabled" in result
        assert "insufficient_history" in result

        # Check skipped test details
        skipped = result["tests_skipped"][0]
        assert skipped["test_name"] == "test_skip_me"
        assert skipped["test_suite"] == "TestSuite"
        assert skipped["success_rate"] == 1.0
        assert skipped["run_count"] == 10

    def test_report_includes_test_counts(self, temp_db_and_filter):
        """Test that report includes proper test counts."""
        db, persistence, smart_filter = temp_db_and_filter

        # Create varied history
        for i in range(10):
            run = ValidationRun(
                timestamp=datetime.now() - timedelta(days=10 - i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=False,
                duration_seconds=10.0,
            )
            run_id = db.insert_validation_run(run)

            # test1: 100% success
            db.insert_test_case_record(
                TestCaseRecord(
                    run_id=run_id,
                    test_name="test1",
                    test_suite="TestSuite",
                    passed=True,
                    duration_seconds=0.1,
                    failure_message=None,
                    skipped=False,
                )
            )

            # test2: 50% success
            db.insert_test_case_record(
                TestCaseRecord(
                    run_id=run_id,
                    test_name="test2",
                    test_suite="TestSuite",
                    passed=i < 5,
                    duration_seconds=0.1,
                    failure_message=None if i < 5 else "Failed",
                    skipped=False,
                )
            )

        result = smart_filter.filter_tests(
            available_tests=[
                ("test1", "TestSuite"),
                ("test2", "TestSuite"),
                ("test_new", "TestSuite"),
            ],
            skip_threshold=0.9,
        )

        # test1 skipped (100%), test2 and test_new should run
        assert len(result["tests_to_run"]) == 2
        assert len(result["tests_skipped"]) == 1


class TestExplicitSelection:
    """Test that filtering respects explicit test selection."""

    def test_explicit_tests_always_run(self, temp_db_and_filter):
        """Test that explicitly selected tests always run despite filtering."""
        db, persistence, smart_filter = temp_db_and_filter

        # Create perfect history
        for i in range(10):
            run = ValidationRun(
                timestamp=datetime.now() - timedelta(days=10 - i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=True,
                duration_seconds=10.0,
            )
            run_id = db.insert_validation_run(run)

            db.insert_test_case_record(
                TestCaseRecord(
                    run_id=run_id,
                    test_name="test_perfect",
                    test_suite="TestSuite",
                    passed=True,
                    duration_seconds=0.1,
                    failure_message=None,
                    skipped=False,
                )
            )

        result = smart_filter.filter_tests(
            available_tests=[("test_perfect", "TestSuite")],
            skip_threshold=0.9,
            explicit_selection=["test_perfect"],
        )

        # Should run despite 100% success rate because explicitly selected
        assert len(result["tests_to_run"]) == 1
        assert len(result["tests_skipped"]) == 0

    def test_pattern_matching_explicit_selection(self, temp_db_and_filter):
        """Test pattern matching for explicit test selection."""
        db, persistence, smart_filter = temp_db_and_filter

        # Create history for multiple tests
        for i in range(10):
            run = ValidationRun(
                timestamp=datetime.now() - timedelta(days=10 - i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=True,
                duration_seconds=10.0,
            )
            run_id = db.insert_validation_run(run)

            for test_name in ["test_auth_login", "test_auth_logout", "test_db_query"]:
                db.insert_test_case_record(
                    TestCaseRecord(
                        run_id=run_id,
                        test_name=test_name,
                        test_suite="TestSuite",
                        passed=True,
                        duration_seconds=0.1,
                        failure_message=None,
                        skipped=False,
                    )
                )

        result = smart_filter.filter_tests(
            available_tests=[
                ("test_auth_login", "TestSuite"),
                ("test_auth_logout", "TestSuite"),
                ("test_db_query", "TestSuite"),
            ],
            skip_threshold=0.9,
            explicit_selection=["test_auth*"],
        )

        # Only auth tests should run (pattern match)
        tests_to_run = result["tests_to_run"]
        assert len(tests_to_run) == 2
        assert ("test_auth_login", "TestSuite") in tests_to_run
        assert ("test_auth_logout", "TestSuite") in tests_to_run
        assert ("test_db_query", "TestSuite") not in tests_to_run
