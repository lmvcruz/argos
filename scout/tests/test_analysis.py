"""
Unit tests for Scout failure analysis engine.

Tests analysis algorithms including:
- Flaky test detection
- Recurring failure detection
- Platform-specific failure detection
- Failure grouping by similarity
- Trend analysis over time
- Actionable recommendation generation
"""

from datetime import datetime, timedelta

from scout.analysis import (
    AnalysisEngine,
    FailureGroup,
    FailureTrend,
    FlakyTest,
    PlatformFailure,
    Recommendation,
)
from scout.failure_parser import Failure, FailureLocation


class TestFlakyTestDetection:
    """Test flaky test detection algorithms."""

    def test_detect_flaky_test_with_mixed_results(self):
        """Test detection of test that passes and fails intermittently."""
        engine = AnalysisEngine()

        # Create test run history: pass, fail, pass, fail, pass
        runs = [
            {"test_name": "test_flaky", "passed": True, "timestamp": datetime.now()},
            {
                "test_name": "test_flaky",
                "passed": False,
                "timestamp": datetime.now() - timedelta(hours=1),
            },
            {
                "test_name": "test_flaky",
                "passed": True,
                "timestamp": datetime.now() - timedelta(hours=2),
            },
            {
                "test_name": "test_flaky",
                "passed": False,
                "timestamp": datetime.now() - timedelta(hours=3),
            },
            {
                "test_name": "test_flaky",
                "passed": True,
                "timestamp": datetime.now() - timedelta(hours=4),
            },
        ]

        flaky_tests = engine.detect_flaky_tests(runs, min_runs=5, flakiness_threshold=0.3)

        assert len(flaky_tests) == 1
        assert flaky_tests[0].test_name == "test_flaky"
        assert flaky_tests[0].pass_rate == 0.6
        assert flaky_tests[0].fail_rate == 0.4
        assert flaky_tests[0].total_runs == 5

    def test_no_flaky_tests_when_always_passing(self):
        """Test that consistently passing tests are not marked as flaky."""
        engine = AnalysisEngine()

        runs = [
            {"test_name": "test_stable", "passed": True, "timestamp": datetime.now()}
            for _ in range(10)
        ]

        flaky_tests = engine.detect_flaky_tests(runs, min_runs=5, flakiness_threshold=0.3)

        assert len(flaky_tests) == 0

    def test_no_flaky_tests_when_always_failing(self):
        """Test that consistently failing tests are not marked as flaky."""
        engine = AnalysisEngine()

        runs = [
            {"test_name": "test_broken", "passed": False, "timestamp": datetime.now()}
            for _ in range(10)
        ]

        flaky_tests = engine.detect_flaky_tests(runs, min_runs=5, flakiness_threshold=0.3)

        assert len(flaky_tests) == 0

    def test_flaky_test_with_multiple_tests(self):
        """Test detection when multiple tests exist."""
        engine = AnalysisEngine()

        runs = [
            # Flaky test
            {"test_name": "test_flaky", "passed": True, "timestamp": datetime.now()},
            {
                "test_name": "test_flaky",
                "passed": False,
                "timestamp": datetime.now() - timedelta(hours=1),
            },
            {
                "test_name": "test_flaky",
                "passed": True,
                "timestamp": datetime.now() - timedelta(hours=2),
            },
            {
                "test_name": "test_flaky",
                "passed": False,
                "timestamp": datetime.now() - timedelta(hours=3),
            },
            {
                "test_name": "test_flaky",
                "passed": True,
                "timestamp": datetime.now() - timedelta(hours=4),
            },
            # Stable test
            {"test_name": "test_stable", "passed": True, "timestamp": datetime.now()},
            {
                "test_name": "test_stable",
                "passed": True,
                "timestamp": datetime.now() - timedelta(hours=1),
            },
            {
                "test_name": "test_stable",
                "passed": True,
                "timestamp": datetime.now() - timedelta(hours=2),
            },
            {
                "test_name": "test_stable",
                "passed": True,
                "timestamp": datetime.now() - timedelta(hours=3),
            },
            {
                "test_name": "test_stable",
                "passed": True,
                "timestamp": datetime.now() - timedelta(hours=4),
            },
        ]

        flaky_tests = engine.detect_flaky_tests(runs, min_runs=5, flakiness_threshold=0.3)

        assert len(flaky_tests) == 1
        assert flaky_tests[0].test_name == "test_flaky"

    def test_insufficient_runs_for_flaky_detection(self):
        """Test that tests with insufficient runs are not analyzed."""
        engine = AnalysisEngine()

        runs = [
            {"test_name": "test_new", "passed": True, "timestamp": datetime.now()},
            {
                "test_name": "test_new",
                "passed": False,
                "timestamp": datetime.now() - timedelta(hours=1),
            },
        ]

        flaky_tests = engine.detect_flaky_tests(runs, min_runs=5, flakiness_threshold=0.3)

        assert len(flaky_tests) == 0


class TestRecurringFailureDetection:
    """Test recurring failure detection."""

    def test_detect_recurring_failure(self):
        """Test detection of test that fails consistently over time."""
        engine = AnalysisEngine()

        failures = [
            Failure(
                test_name="test_broken",
                test_file="test_math.py",
                message="assert 2 + 2 == 5",
            )
            for _ in range(5)
        ]

        recurring = engine.detect_recurring_failures(failures, min_occurrences=3)

        assert len(recurring) == 1
        assert recurring[0].test_name == "test_broken"
        assert recurring[0].occurrence_count == 5

    def test_no_recurring_failures_below_threshold(self):
        """Test that failures below threshold are not flagged."""
        engine = AnalysisEngine()

        failures = [
            Failure(
                test_name="test_occasional",
                test_file="test_math.py",
                message="assert 2 + 2 == 5",
            )
            for _ in range(2)
        ]

        recurring = engine.detect_recurring_failures(failures, min_occurrences=3)

        assert len(recurring) == 0

    def test_multiple_recurring_failures(self):
        """Test detection of multiple recurring failures."""
        engine = AnalysisEngine()

        failures = [
            Failure(
                test_name="test_broken1",
                test_file="test_math.py",
                message="assert 2 + 2 == 5",
            )
            for _ in range(5)
        ] + [
            Failure(
                test_name="test_broken2",
                test_file="test_logic.py",
                message="assert True is False",
            )
            for _ in range(4)
        ]

        recurring = engine.detect_recurring_failures(failures, min_occurrences=3)

        assert len(recurring) == 2
        test_names = {r.test_name for r in recurring}
        assert test_names == {"test_broken1", "test_broken2"}


class TestPlatformSpecificFailures:
    """Test platform-specific failure detection."""

    def test_detect_windows_only_failure(self):
        """Test detection of failure that only occurs on Windows."""
        engine = AnalysisEngine()

        runs = [
            {"test_name": "test_path", "platform": "windows", "passed": False},
            {"test_name": "test_path", "platform": "linux", "passed": True},
            {"test_name": "test_path", "platform": "macos", "passed": True},
        ]

        platform_failures = engine.detect_platform_specific_failures(runs)

        assert len(platform_failures) == 1
        assert platform_failures[0].test_name == "test_path"
        assert platform_failures[0].failing_platforms == ["windows"]
        assert platform_failures[0].passing_platforms == ["linux", "macos"]

    def test_detect_linux_only_failure(self):
        """Test detection of failure that only occurs on Linux."""
        engine = AnalysisEngine()

        runs = [
            {"test_name": "test_signal", "platform": "windows", "passed": True},
            {"test_name": "test_signal", "platform": "linux", "passed": False},
            {"test_name": "test_signal", "platform": "macos", "passed": True},
        ]

        platform_failures = engine.detect_platform_specific_failures(runs)

        assert len(platform_failures) == 1
        assert platform_failures[0].test_name == "test_signal"
        assert platform_failures[0].failing_platforms == ["linux"]

    def test_no_platform_specific_when_all_fail(self):
        """Test that tests failing on all platforms are not flagged."""
        engine = AnalysisEngine()

        runs = [
            {"test_name": "test_broken", "platform": "windows", "passed": False},
            {"test_name": "test_broken", "platform": "linux", "passed": False},
            {"test_name": "test_broken", "platform": "macos", "passed": False},
        ]

        platform_failures = engine.detect_platform_specific_failures(runs)

        assert len(platform_failures) == 0

    def test_no_platform_specific_when_all_pass(self):
        """Test that tests passing on all platforms are not flagged."""
        engine = AnalysisEngine()

        runs = [
            {"test_name": "test_good", "platform": "windows", "passed": True},
            {"test_name": "test_good", "platform": "linux", "passed": True},
            {"test_name": "test_good", "platform": "macos", "passed": True},
        ]

        platform_failures = engine.detect_platform_specific_failures(runs)

        assert len(platform_failures) == 0


class TestFailureGrouping:
    """Test failure grouping by similarity."""

    def test_group_failures_by_same_message(self):
        """Test grouping of failures with identical messages."""
        engine = AnalysisEngine()

        failures = [
            Failure(
                test_name="test_math1",
                test_file="test_math.py",
                message="assert 2 + 2 == 5",
            ),
            Failure(
                test_name="test_math2",
                test_file="test_math.py",
                message="assert 2 + 2 == 5",
            ),
            Failure(
                test_name="test_math3",
                test_file="test_math.py",
                message="assert 2 + 2 == 5",
            ),
        ]

        groups = engine.group_failures_by_similarity(failures)

        assert len(groups) == 1
        assert len(groups[0].failures) == 3
        assert groups[0].common_message == "assert 2 + 2 == 5"

    def test_group_failures_by_same_location(self):
        """Test grouping of failures at the same location."""
        engine = AnalysisEngine()

        failures = [
            Failure(
                test_name="test1",
                test_file="test_math.py",
                message="different message 1",
                location=FailureLocation(file="test_math.py", line=42),
            ),
            Failure(
                test_name="test2",
                test_file="test_math.py",
                message="different message 2",
                location=FailureLocation(file="test_math.py", line=42),
            ),
        ]

        groups = engine.group_failures_by_similarity(failures)

        assert len(groups) == 1
        assert len(groups[0].failures) == 2
        assert groups[0].common_location == "test_math.py:42"

    def test_group_failures_by_same_type(self):
        """Test grouping of failures by exception type."""
        engine = AnalysisEngine()

        failures = [
            Failure(
                test_name="test1",
                test_file="test_math.py",
                message="division by zero",
                failure_type="ZeroDivisionError",
            ),
            Failure(
                test_name="test2",
                test_file="test_math.py",
                message="cannot divide by zero",
                failure_type="ZeroDivisionError",
            ),
            Failure(
                test_name="test3",
                test_file="test_logic.py",
                message="assertion failed",
                failure_type="AssertionError",
            ),
        ]

        groups = engine.group_failures_by_similarity(failures)

        # Should have 2 groups: one for ZeroDivisionError, one for AssertionError
        assert len(groups) == 2
        zero_div_group = [g for g in groups if g.failure_type == "ZeroDivisionError"][0]
        assert len(zero_div_group.failures) == 2

    def test_no_grouping_for_unique_failures(self):
        """Test that completely different failures are not grouped."""
        engine = AnalysisEngine()

        failures = [
            Failure(
                test_name="test1",
                test_file="test_math.py",
                message="error 1",
                failure_type="Error1",
            ),
            Failure(
                test_name="test2",
                test_file="test_logic.py",
                message="error 2",
                failure_type="Error2",
            ),
        ]

        groups = engine.group_failures_by_similarity(failures)

        # Each failure in its own group
        assert len(groups) == 2
        assert all(len(g.failures) == 1 for g in groups)


class TestTrendAnalysis:
    """Test trend analysis over time."""

    def test_detect_increasing_failure_trend(self):
        """Test detection of increasing failure rate over time."""
        engine = AnalysisEngine()

        # Failure rate increasing: 10%, 20%, 30%, 40%, 50%
        runs = [
            {"timestamp": datetime.now() - timedelta(days=4), "total": 10, "failed": 1},
            {"timestamp": datetime.now() - timedelta(days=3), "total": 10, "failed": 2},
            {"timestamp": datetime.now() - timedelta(days=2), "total": 10, "failed": 3},
            {"timestamp": datetime.now() - timedelta(days=1), "total": 10, "failed": 4},
            {"timestamp": datetime.now(), "total": 10, "failed": 5},
        ]

        trend = engine.analyze_failure_trend(runs)

        assert trend.direction == "increasing"
        assert trend.trend_strength > 0.3  # Moderate to strong positive trend (0.4 normalized)

    def test_detect_decreasing_failure_trend(self):
        """Test detection of decreasing failure rate over time."""
        engine = AnalysisEngine()

        # Failure rate decreasing: 50%, 40%, 30%, 20%, 10%
        runs = [
            {"timestamp": datetime.now() - timedelta(days=4), "total": 10, "failed": 5},
            {"timestamp": datetime.now() - timedelta(days=3), "total": 10, "failed": 4},
            {"timestamp": datetime.now() - timedelta(days=2), "total": 10, "failed": 3},
            {"timestamp": datetime.now() - timedelta(days=1), "total": 10, "failed": 2},
            {"timestamp": datetime.now(), "total": 10, "failed": 1},
        ]

        trend = engine.analyze_failure_trend(runs)

        assert trend.direction == "decreasing"
        assert trend.trend_strength > 0.3  # Moderate to strong negative trend (0.4 normalized)

    def test_detect_stable_trend(self):
        """Test detection of stable failure rate."""
        engine = AnalysisEngine()

        # Stable failure rate: 20% ± small variation
        runs = [
            {"timestamp": datetime.now() - timedelta(days=i), "total": 10, "failed": 2}
            for i in range(5)
        ]

        trend = engine.analyze_failure_trend(runs)

        assert trend.direction == "stable"

    def test_insufficient_data_for_trend(self):
        """Test that insufficient data returns None or stable trend."""
        engine = AnalysisEngine()

        runs = [{"timestamp": datetime.now(), "total": 10, "failed": 2}]

        trend = engine.analyze_failure_trend(runs)

        assert trend.direction == "stable" or trend is None


class TestRecommendationGeneration:
    """Test actionable recommendation generation."""

    def test_recommendation_for_flaky_test(self):
        """Test recommendation generation for flaky tests."""
        engine = AnalysisEngine()

        flaky_test = FlakyTest(
            test_name="test_timing_sensitive",
            pass_rate=0.7,
            fail_rate=0.3,
            total_runs=10,
        )

        recommendations = engine.generate_recommendations(flaky_tests=[flaky_test])

        assert len(recommendations) > 0
        rec = recommendations[0]
        assert rec.category == "flaky_test"
        assert "test_timing_sensitive" in rec.description
        assert rec.priority in ["high", "medium", "low"]
        assert len(rec.suggested_actions) > 0

    def test_recommendation_for_recurring_failure(self):
        """Test recommendation for recurring failures."""
        engine = AnalysisEngine()

        failure = Failure(
            test_name="test_broken",
            test_file="test_math.py",
            message="assert 2 + 2 == 5",
        )

        recommendations = engine.generate_recommendations(recurring_failures=[failure] * 5)

        assert len(recommendations) > 0
        rec = recommendations[0]
        assert rec.category == "recurring_failure"
        assert "test_broken" in rec.description

    def test_recommendation_for_platform_specific_failure(self):
        """Test recommendation for platform-specific failures."""
        engine = AnalysisEngine()

        platform_failure = PlatformFailure(
            test_name="test_path_separator",
            failing_platforms=["windows"],
            passing_platforms=["linux", "macos"],
        )

        recommendations = engine.generate_recommendations(platform_failures=[platform_failure])

        assert len(recommendations) > 0
        rec = recommendations[0]
        assert rec.category == "platform_specific"
        assert "windows" in rec.description.lower()

    def test_recommendation_for_increasing_trend(self):
        """Test recommendation for increasing failure trend."""
        engine = AnalysisEngine()

        trend = FailureTrend(direction="increasing", trend_strength=0.8)

        recommendations = engine.generate_recommendations(failure_trend=trend)

        assert len(recommendations) > 0
        rec = recommendations[0]
        assert rec.category == "trend"
        assert "increasing" in rec.description.lower()
        assert rec.priority == "high"

    def test_no_recommendations_for_healthy_state(self):
        """Test that no recommendations are generated for healthy state."""
        engine = AnalysisEngine()

        recommendations = engine.generate_recommendations()

        assert len(recommendations) == 0

    def test_multiple_recommendations_prioritized(self):
        """Test that multiple recommendations are prioritized correctly."""
        engine = AnalysisEngine()

        flaky_test = FlakyTest(test_name="test_flaky", pass_rate=0.5, fail_rate=0.5, total_runs=10)
        trend = FailureTrend(direction="increasing", trend_strength=0.9)

        recommendations = engine.generate_recommendations(
            flaky_tests=[flaky_test], failure_trend=trend
        )

        assert len(recommendations) >= 2
        # High priority recommendations should come first
        priorities = [r.priority for r in recommendations]
        assert priorities[0] in ["high", "medium"]


class TestFailureGroupDataclass:
    """Test FailureGroup dataclass."""

    def test_failure_group_creation(self):
        """Test creation of failure group."""
        failures = [
            Failure(
                test_name="test1",
                test_file="test_math.py",
                message="error",
            ),
            Failure(
                test_name="test2",
                test_file="test_math.py",
                message="error",
            ),
        ]

        group = FailureGroup(
            failures=failures,
            common_message="error",
            common_location=None,
            failure_type="AssertionError",
        )

        assert len(group.failures) == 2
        assert group.common_message == "error"
        assert group.failure_type == "AssertionError"


class TestFlakyTestDataclass:
    """Test FlakyTest dataclass."""

    def test_flaky_test_creation(self):
        """Test creation of flaky test."""
        flaky = FlakyTest(
            test_name="test_flaky",
            pass_rate=0.6,
            fail_rate=0.4,
            total_runs=10,
        )

        assert flaky.test_name == "test_flaky"
        assert flaky.pass_rate == 0.6
        assert flaky.fail_rate == 0.4
        assert flaky.total_runs == 10


class TestPlatformFailureDataclass:
    """Test PlatformFailure dataclass."""

    def test_platform_failure_creation(self):
        """Test creation of platform failure."""
        pf = PlatformFailure(
            test_name="test_platform",
            failing_platforms=["windows"],
            passing_platforms=["linux", "macos"],
        )

        assert pf.test_name == "test_platform"
        assert pf.failing_platforms == ["windows"]
        assert pf.passing_platforms == ["linux", "macos"]


class TestRecommendationDataclass:
    """Test Recommendation dataclass."""

    def test_recommendation_creation(self):
        """Test creation of recommendation."""
        rec = Recommendation(
            category="flaky_test",
            description="Fix flaky test",
            priority="high",
            suggested_actions=["Add explicit waits", "Use mocking"],
        )

        assert rec.category == "flaky_test"
        assert rec.description == "Fix flaky test"
        assert rec.priority == "high"
        assert len(rec.suggested_actions) == 2


class TestFailureTrendDataclass:
    """Test FailureTrend dataclass."""

    def test_failure_trend_creation(self):
        """Test creation of failure trend."""
        trend = FailureTrend(
            direction="increasing",
            trend_strength=0.8,
        )

        assert trend.direction == "increasing"
        assert trend.trend_strength == 0.8
