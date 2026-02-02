"""
Failure analysis engine for Scout.

Analyzes test failures to detect patterns and provide actionable insights:
- Flaky test detection
- Recurring failure detection
- Platform-specific failure detection
- Failure grouping by similarity
- Trend analysis over time
- Recommendation generation
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

from scout.failure_parser import Failure


@dataclass
class FlakyTest:
    """
    Represents a flaky test.

    Args:
        test_name: Name of the flaky test
        pass_rate: Percentage of runs that passed (0.0-1.0)
        fail_rate: Percentage of runs that failed (0.0-1.0)
        total_runs: Total number of runs analyzed
    """

    test_name: str
    pass_rate: float
    fail_rate: float
    total_runs: int


@dataclass
class FailureGroup:
    """
    Represents a group of similar failures.

    Args:
        failures: List of failures in this group
        common_message: Common error message across failures
        common_location: Common file:line location
        failure_type: Common exception/error type
    """

    failures: List[Failure]
    common_message: Optional[str] = None
    common_location: Optional[str] = None
    failure_type: Optional[str] = None


@dataclass
class FailureTrend:
    """
    Represents a failure trend over time.

    Args:
        direction: Trend direction ('increasing', 'decreasing', 'stable')
        trend_strength: Strength of trend (0.0-1.0)
    """

    direction: str
    trend_strength: float


@dataclass
class PlatformFailure:
    """
    Represents a platform-specific failure.

    Args:
        test_name: Name of the test
        failing_platforms: List of platforms where test fails
        passing_platforms: List of platforms where test passes
    """

    test_name: str
    failing_platforms: List[str]
    passing_platforms: List[str]


@dataclass
class Recommendation:
    """
    Represents an actionable recommendation.

    Args:
        category: Category of recommendation
        description: Human-readable description
        priority: Priority level ('high', 'medium', 'low')
        suggested_actions: List of suggested actions
    """

    category: str
    description: str
    priority: str
    suggested_actions: List[str]


class AnalysisEngine:
    """
    Engine for analyzing test failures and generating insights.

    Provides methods for:
    - Detecting flaky tests
    - Identifying recurring failures
    - Finding platform-specific failures
    - Grouping similar failures
    - Analyzing failure trends
    - Generating recommendations
    """

    def detect_flaky_tests(
        self,
        runs: List[Dict],
        min_runs: int = 5,
        flakiness_threshold: float = 0.3,
    ) -> List[FlakyTest]:
        """
        Detect flaky tests from test run history.

        A test is considered flaky if:
        1. It has at least min_runs executions
        2. Its failure rate is between flakiness_threshold and (1 - flakiness_threshold)

        Args:
            runs: List of test run records with 'test_name', 'passed', 'timestamp'
            min_runs: Minimum number of runs required for analysis
            flakiness_threshold: Minimum failure rate to consider flaky

        Returns:
            List of detected flaky tests
        """
        # Group runs by test name
        test_runs = defaultdict(list)
        for run in runs:
            test_runs[run["test_name"]].append(run)

        flaky_tests = []

        for test_name, test_run_list in test_runs.items():
            if len(test_run_list) < min_runs:
                continue

            # Calculate pass/fail rates
            passed_count = sum(1 for r in test_run_list if r["passed"])
            failed_count = len(test_run_list) - passed_count

            pass_rate = passed_count / len(test_run_list)
            fail_rate = failed_count / len(test_run_list)

            # Check if flaky (neither always passing nor always failing)
            if flakiness_threshold <= fail_rate <= (1 - flakiness_threshold):
                flaky_tests.append(
                    FlakyTest(
                        test_name=test_name,
                        pass_rate=pass_rate,
                        fail_rate=fail_rate,
                        total_runs=len(test_run_list),
                    )
                )

        return flaky_tests

    def detect_recurring_failures(
        self,
        failures: List[Failure],
        min_occurrences: int = 3,
    ) -> List[Failure]:
        """
        Detect recurring failures.

        Args:
            failures: List of test failures
            min_occurrences: Minimum number of occurrences to consider recurring

        Returns:
            List of recurring failures with occurrence counts
        """
        # Count occurrences of each test failure
        failure_counts = defaultdict(int)
        failure_examples = {}

        for failure in failures:
            failure_counts[failure.test_name] += 1
            if failure.test_name not in failure_examples:
                failure_examples[failure.test_name] = failure

        # Filter recurring failures
        recurring = []
        for test_name, count in failure_counts.items():
            if count >= min_occurrences:
                # Create a failure object with occurrence count
                failure = failure_examples[test_name]
                # Store occurrence count as attribute
                failure.occurrence_count = count
                recurring.append(failure)

        return recurring

    def detect_platform_specific_failures(
        self,
        runs: List[Dict],
    ) -> List[PlatformFailure]:
        """
        Detect platform-specific failures.

        Args:
            runs: List of test runs with 'test_name', 'platform', 'passed'

        Returns:
            List of platform-specific failures
        """
        # Group runs by test name
        test_runs = defaultdict(list)
        for run in runs:
            test_runs[run["test_name"]].append(run)

        platform_failures = []

        for test_name, test_run_list in test_runs.items():
            # Get platforms where test passed and failed
            passing_platforms = set()
            failing_platforms = set()

            for run in test_run_list:
                platform = run["platform"]
                if run["passed"]:
                    passing_platforms.add(platform)
                else:
                    failing_platforms.add(platform)

            # Platform-specific if fails on some platforms but passes on others
            if failing_platforms and passing_platforms:
                platform_failures.append(
                    PlatformFailure(
                        test_name=test_name,
                        failing_platforms=sorted(list(failing_platforms)),
                        passing_platforms=sorted(list(passing_platforms)),
                    )
                )

        return platform_failures

    def group_failures_by_similarity(
        self,
        failures: List[Failure],
    ) -> List[FailureGroup]:
        """
        Group failures by similarity.

        Failures are grouped by:
        1. Same error message
        2. Same location (file:line)
        3. Same exception type

        Args:
            failures: List of test failures

        Returns:
            List of failure groups
        """
        # Group by multiple criteria
        groups_by_message = defaultdict(list)
        groups_by_location = defaultdict(list)
        groups_by_type = defaultdict(list)

        for failure in failures:
            # Group by message
            if failure.message:
                groups_by_message[failure.message].append(failure)

            # Group by location
            if failure.location:
                location_key = f"{failure.location.file}:{failure.location.line}"
                groups_by_location[location_key].append(failure)

            # Group by type
            if failure.failure_type:
                groups_by_type[failure.failure_type].append(failure)

        # Create FailureGroup objects
        groups = []

        # Prioritize message grouping
        for message, failure_list in groups_by_message.items():
            if len(failure_list) > 1:
                groups.append(
                    FailureGroup(
                        failures=failure_list,
                        common_message=message,
                        failure_type=(
                            failure_list[0].failure_type if failure_list[0].failure_type else None
                        ),
                    )
                )
                continue

        # Then location grouping (for different messages at same location)
        for location, failure_list in groups_by_location.items():
            if len(failure_list) > 1:
                # Check if not already grouped by message
                already_grouped = any(any(f in g.failures for f in failure_list) for g in groups)
                if not already_grouped:
                    groups.append(
                        FailureGroup(
                            failures=failure_list,
                            common_location=location,
                            failure_type=(
                                failure_list[0].failure_type
                                if failure_list[0].failure_type
                                else None
                            ),
                        )
                    )
                    continue

        # Finally, group by type (for different messages/locations)
        for failure_type, failure_list in groups_by_type.items():
            if len(failure_list) > 1:
                # Check if not already grouped
                already_grouped = any(any(f in g.failures for f in failure_list) for g in groups)
                if not already_grouped:
                    groups.append(
                        FailureGroup(
                            failures=failure_list,
                            failure_type=failure_type,
                        )
                    )
                    continue

        # Add individual failures not grouped
        grouped_failures = []
        for group in groups:
            grouped_failures.extend(group.failures)

        for failure in failures:
            if failure not in grouped_failures:
                groups.append(
                    FailureGroup(
                        failures=[failure],
                        common_message=failure.message,
                        failure_type=failure.failure_type,
                    )
                )

        return groups

    def analyze_failure_trend(
        self,
        runs: List[Dict],
    ) -> Optional[FailureTrend]:
        """
        Analyze failure trend over time.

        Args:
            runs: List of test runs with 'timestamp', 'total', 'failed'

        Returns:
            FailureTrend object or None if insufficient data
        """
        if len(runs) < 2:
            return FailureTrend(direction="stable", trend_strength=0.0)

        # Sort by timestamp
        sorted_runs = sorted(runs, key=lambda x: x["timestamp"])

        # Calculate failure rates
        failure_rates = [r["failed"] / r["total"] for r in sorted_runs]

        # Calculate trend using linear regression slope
        n = len(failure_rates)
        x_values = list(range(n))
        x_mean = sum(x_values) / n
        y_mean = sum(failure_rates) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, failure_rates))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return FailureTrend(direction="stable", trend_strength=0.0)

        slope = numerator / denominator

        # Normalize slope to 0-1 range based on maximum possible change
        # For n data points with values 0-1, max slope is roughly 1/(n-1)
        max_slope = 1.0 / (n - 1) if n > 1 else 1.0
        normalized_strength = min(abs(slope) / max_slope, 1.0)

        # Determine direction and strength
        if abs(slope) < 0.01:  # Threshold for stable
            return FailureTrend(direction="stable", trend_strength=normalized_strength)
        elif slope > 0:
            return FailureTrend(direction="increasing", trend_strength=normalized_strength)
        else:
            return FailureTrend(direction="decreasing", trend_strength=normalized_strength)

    def generate_recommendations(
        self,
        flaky_tests: Optional[List[FlakyTest]] = None,
        recurring_failures: Optional[List[Failure]] = None,
        platform_failures: Optional[List[PlatformFailure]] = None,
        failure_trend: Optional[FailureTrend] = None,
    ) -> List[Recommendation]:
        """
        Generate actionable recommendations.

        Args:
            flaky_tests: List of detected flaky tests
            recurring_failures: List of recurring failures
            platform_failures: List of platform-specific failures
            failure_trend: Failure trend analysis

        Returns:
            List of recommendations
        """
        recommendations = []

        # Recommendations for flaky tests
        if flaky_tests:
            for flaky in flaky_tests:
                priority = "high" if flaky.fail_rate > 0.4 else "medium"
                recommendations.append(
                    Recommendation(
                        category="flaky_test",
                        description=f"Flaky test detected: {flaky.test_name} "
                        f"(fails {flaky.fail_rate:.0%} of the time)",
                        priority=priority,
                        suggested_actions=[
                            "Add explicit waits or timeouts",
                            "Use mocking for external dependencies",
                            "Check for race conditions",
                            "Review test isolation",
                        ],
                    )
                )

        # Recommendations for recurring failures
        if recurring_failures:
            for failure in recurring_failures:
                recommendations.append(
                    Recommendation(
                        category="recurring_failure",
                        description=f"Recurring failure: {failure.test_name} "
                        f"(failed {getattr(failure, 'occurrence_count', 0)} times)",
                        priority="high",
                        suggested_actions=[
                            "Fix the underlying bug causing the failure",
                            "Review test implementation",
                            "Check for environment-specific issues",
                        ],
                    )
                )

        # Recommendations for platform-specific failures
        if platform_failures:
            for pf in platform_failures:
                platforms_str = ", ".join(pf.failing_platforms)
                recommendations.append(
                    Recommendation(
                        category="platform_specific",
                        description=f"Platform-specific failure: {pf.test_name} "
                        f"fails on {platforms_str}",
                        priority="medium",
                        suggested_actions=[
                            f"Review platform-specific code for {platforms_str}",
                            "Check for path separator issues",
                            "Verify environment variables",
                            "Review file system operations",
                        ],
                    )
                )

        # Recommendations for failure trends
        if failure_trend and failure_trend.direction == "increasing":
            priority = "high" if failure_trend.trend_strength > 0.5 else "medium"
            recommendations.append(
                Recommendation(
                    category="trend",
                    description="Increasing failure trend detected",
                    priority=priority,
                    suggested_actions=[
                        "Review recent code changes",
                        "Check for regression in dependencies",
                        "Analyze test stability over time",
                        "Consider rollback if critical",
                    ],
                )
            )

        # Sort by priority (high, medium, low)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 3))

        return recommendations
