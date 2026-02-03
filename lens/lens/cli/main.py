"""
Lens CLI - Main entry point.

Provides commands for analyzing CI health, generating reports,
and identifying improvement opportunities.
"""

import argparse
import os
import sys
from pathlib import Path

from lens.analytics.ci_health import CIHealthAnalyzer
from lens.analytics.test_execution import TestExecutionAnalyzer
from lens.reports.html_generator import HTMLReportGenerator
from lens.reports.test_execution_report import TestExecutionReportGenerator


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="lens",
        description="CI Analytics and Visualization Tool",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="lens 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'report' command
    report_parser = subparsers.add_parser(
        "report",
        help="Generate reports",
    )
    report_parser.add_argument(
        "report_type",
        choices=["ci-health", "platform-breakdown", "flaky-tests", "test-execution"],
        help="Type of report to generate",
    )
    report_parser.add_argument(
        "--db",
        default="scout.db",
        help="Path to Scout database for CI reports or .anvil/history.db for test reports",
    )
    report_parser.add_argument(
        "--workflow",
        help="Filter by workflow name (CI reports only)",
    )
    report_parser.add_argument(
        "--window",
        type=int,
        default=30,
        help="Time window in days (default: 30)",
    )
    report_parser.add_argument(
        "--threshold",
        type=float,
        default=0.10,
        help="Flaky test threshold for test-execution report (default: 0.10 = 10%%)",
    )
    report_parser.add_argument(
        "--format",
        choices=["console", "html"],
        default="console",
        help="Output format (default: console)",
    )
    report_parser.add_argument(
        "--output",
        help="Output file path (required for HTML format)",
    )

    # 'analyze' command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze CI metrics",
    )
    analyze_parser.add_argument(
        "--db",
        default="scout.db",
        help="Path to Scout database (default: scout.db)",
    )
    analyze_parser.add_argument(
        "--workflow",
        help="Filter by workflow name",
    )
    analyze_parser.add_argument(
        "--window",
        type=int,
        default=30,
        help="Time window in days (default: 30)",
    )

    return parser


def handle_report_command(args) -> int:
    """Handle 'report' command."""
    try:
        # Handle test execution reports
        if args.report_type == "test-execution":
            return handle_test_execution_report(args)

        # Handle CI health reports
        analyzer = CIHealthAnalyzer(args.db)

        if args.report_type == "ci-health":
            # Get all analytics data
            summary = analyzer.get_ci_health_summary(
                days=args.window, workflow_name=args.workflow
            )
            platform_breakdown = analyzer.get_platform_breakdown(
                days=args.window, workflow_name=args.workflow
            )
            trends = analyzer.get_failure_trends(
                days=args.window, workflow_name=args.workflow
            )
            flaky_tests = analyzer.get_flaky_tests(days=args.window)
            slowest_jobs = analyzer.get_slowest_jobs(
                days=args.window, workflow_name=args.workflow
            )

            if args.format == "html":
                if not args.output:
                    print(
                        "Error: --output required for HTML format", file=sys.stderr
                    )
                    return 1

                generator = HTMLReportGenerator()
                output_path = generator.generate_health_report(
                    summary,
                    platform_breakdown,
                    trends,
                    flaky_tests,
                    slowest_jobs,
                    args.output,
                )
                print(f"✓ HTML report generated: {output_path}")
                print(f"\nOpen in browser: file://{Path(output_path).absolute()}")

            else:  # console
                print_ci_health_summary(
                    summary, platform_breakdown, trends, flaky_tests, slowest_jobs
                )

        elif args.report_type == "platform-breakdown":
            platform_breakdown = analyzer.get_platform_breakdown(
                days=args.window, workflow_name=args.workflow
            )
            print_platform_breakdown(platform_breakdown, args.window)

        elif args.report_type == "flaky-tests":
            flaky_tests = analyzer.get_flaky_tests(days=args.window)
            print_flaky_tests(flaky_tests, args.window)

        analyzer.close()
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def handle_analyze_command(args) -> int:
    """Handle 'analyze' command."""
    try:
        analyzer = CIHealthAnalyzer(args.db)

        summary = analyzer.get_ci_health_summary(
            days=args.window, workflow_name=args.workflow
        )

        print(f"\n=== CI Health Analysis ({summary['time_window']}) ===\n")
        print(f"Total Runs: {summary['total_runs']}")
        print(f"Successful: {summary['successful_runs']}")
        print(f"Failed: {summary['failed_runs']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Avg Duration: {summary['avg_duration_seconds'] / 60:.1f} minutes")

        # Get flaky tests
        flaky = analyzer.get_flaky_tests(days=args.window)
        if flaky:
            print(f"\n⚠️  Found {len(flaky)} flaky test(s)")
            print("   Run 'lens report flaky-tests' for details")

        # Get platform breakdown
        platforms = analyzer.get_platform_breakdown(
            days=args.window, workflow_name=args.workflow
        )
        print(f"\nPlatforms tested: {', '.join(platforms.keys())}")

        analyzer.close()
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def print_ci_health_summary(summary, platform_breakdown, trends, flaky_tests, slowest_jobs):
    """Print CI health summary to console."""
    print(f"\n{'=' * 70}")
    print(f"{'CI HEALTH REPORT':^70}")
    print(f"{'=' * 70}\n")

    print(f"📊 OVERALL HEALTH ({summary['time_window']})\n")
    print(f"  Total Runs:       {summary['total_runs']}")
    print(f"  Successful:       {summary['successful_runs']}")
    print(f"  Failed:           {summary['failed_runs']}")
    print(f"  Success Rate:     {summary['success_rate']:.1f}%")
    print(f"  Avg Duration:     {summary['avg_duration_seconds'] / 60:.1f}m\n")

    # Platform breakdown
    if platform_breakdown:
        print(f"🖥️  PLATFORM BREAKDOWN\n")
        for platform, stats in sorted(platform_breakdown.items()):
            success_rate = stats['success_rate']
            status_icon = "✓" if success_rate >= 80 else "✗"
            print(f"  {status_icon} {platform}")
            print(f"     Jobs: {stats['total_jobs']} | Success: {stats['successful_jobs']} | Failed: {stats['failed_jobs']}")
            print(f"     Success Rate: {success_rate:.1f}% | Avg Duration: {stats['avg_duration']:.0f}s")
            print()

    # Flaky tests
    if flaky_tests:
        print(f"⚠️  FLAKY TESTS ({len(flaky_tests)} detected)\n")
        for i, test in enumerate(flaky_tests[:10], 1):
            platforms = ", ".join(test['platforms'])
            print(f"  {i}. {test['test_name']}")
            print(f"     Runs: {test['total_runs']} | Failures: {test['failures']} | Rate: {test['failure_rate']:.1f}%")
            print(f"     Platforms: {platforms}")
            print()
        if len(flaky_tests) > 10:
            print(f"  ... and {len(flaky_tests) - 10} more\n")

    # Slowest jobs
    if slowest_jobs:
        print(f"🐌 SLOWEST JOBS (Top {len(slowest_jobs)})\n")
        for i, job in enumerate(slowest_jobs, 1):
            duration_min = job['duration_seconds'] / 60
            print(f"  {i}. {job['job_name']} ({job['platform']})")
            print(f"     Duration: {duration_min:.1f}m | Status: {job['status']}")
            print()

    print(f"{'=' * 70}\n")


def print_platform_breakdown(platform_breakdown, days):
    """Print platform breakdown to console."""
    print(f"\n=== Platform Breakdown (Last {days} days) ===\n")

    if not platform_breakdown:
        print("No platform data available.\n")
        return

    for platform, stats in sorted(platform_breakdown.items()):
        success_rate = stats['success_rate']
        status_icon = "✓" if success_rate >= 80 else "✗"

        print(f"{status_icon} {platform}")
        print(f"  Total Jobs:    {stats['total_jobs']}")
        print(f"  Successful:    {stats['successful_jobs']}")
        print(f"  Failed:        {stats['failed_jobs']}")
        print(f"  Success Rate:  {success_rate:.1f}%")
        print(f"  Avg Duration:  {stats['avg_duration']:.0f}s")
        print()


def print_flaky_tests(flaky_tests, days):
    """Print flaky tests to console."""
    print(f"\n=== Flaky Tests (Last {days} days) ===\n")

    if not flaky_tests:
        print("✅ No flaky tests detected!\n")
        return

    print(f"Found {len(flaky_tests)} flaky test(s):\n")

    for i, test in enumerate(flaky_tests, 1):
        platforms = ", ".join(test['platforms'])
        print(f"{i}. {test['test_name']}")
        print(f"   Total Runs:    {test['total_runs']}")
        print(f"   Failures:      {test['failures']}")
        print(f"   Failure Rate:  {test['failure_rate']:.1f}%")
        print(f"   Platforms:     {platforms}")
        print()


def handle_test_execution_report(args) -> int:
    """Handle test execution report generation."""
    try:
        # Determine database path
        db_path = args.db if args.db != "scout.db" else ".anvil/history.db"

        analyzer = TestExecutionAnalyzer(db_path)

        # Get analytics data
        summary = analyzer.get_execution_summary(days=args.window)
        flaky_tests = analyzer.get_flaky_tests(
            threshold=args.threshold, window=args.window
        )
        trends = analyzer.get_test_trends(days=args.window)
        slowest_tests = analyzer.get_slowest_tests(limit=10)

        if args.format == "html":
            if not args.output:
                print(
                    "Error: --output is required for HTML format", file=sys.stderr
                )
                return 1

            generator = TestExecutionReportGenerator()
            generator.generate_test_summary_report(
                summary=summary,
                flaky_tests=flaky_tests,
                trends=trends,
                slowest_tests=slowest_tests,
                output_path=args.output,
            )
            print(f"✅ Test execution report generated: {args.output}")
            return 0

        else:
            # Console format
            print_test_execution_summary(
                summary, flaky_tests, trends, slowest_tests
            )
            return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error generating test execution report: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def print_test_execution_summary(summary, flaky_tests, trends, slowest_tests):
    """Print test execution summary to console."""
    print(f"\n{'=' * 70}")
    print(f"TEST EXECUTION REPORT (Last {summary['window_days']} days)")
    print(f"{'=' * 70}\n")

    # Summary metrics
    print(f"📊 SUMMARY\n")
    print(f"  Total Executions: {summary['total_executions']}")
    print(f"  Unique Tests:     {summary['unique_tests']}")
    print(f"  Success Rate:     {summary['success_rate']:.1f}%")
    print(f"  Avg Duration:     {summary['avg_duration']:.2f}s\n")

    # Status breakdown
    print(f"  Status Breakdown:")
    print(f"    ✓ Passed:       {summary['passed']}")
    print(f"    ✗ Failed:       {summary['failed']}")
    print(f"    ⊘ Skipped:      {summary['skipped']}")
    if summary.get("error", 0) > 0:
        print(f"    ⚠ Error:        {summary['error']}")
    print()

    # Flaky tests
    if flaky_tests:
        print(f"⚠️  FLAKY TESTS ({len(flaky_tests)} detected)\n")
        for i, test in enumerate(flaky_tests[:10], 1):
            # Shorten test ID for display
            entity_id = test["entity_id"]
            if len(entity_id) > 70:
                entity_id = "..." + entity_id[-67:]

            print(f"  {i}. {entity_id}")
            print(f"     Runs: {test['total_runs']} | Passed: {test['passed']} | Failed: {test['failed']}")
            print(f"     Failure Rate: {test['failure_rate']*100:.1f}% | Avg: {test['avg_duration']:.2f}s")
            print()
        if len(flaky_tests) > 10:
            print(f"  ... and {len(flaky_tests) - 10} more\n")
    else:
        print(f"✅ FLAKY TESTS\n\n  No flaky tests detected!\n")

    # Slowest tests
    if slowest_tests:
        print(f"🐌 SLOWEST TESTS (Top {len(slowest_tests)})\n")
        for i, test in enumerate(slowest_tests, 1):
            entity_id = test["entity_id"]
            if len(entity_id) > 70:
                entity_id = "..." + entity_id[-67:]

            print(f"  {i}. {entity_id}")
            print(f"     Avg Duration: {test['avg_duration']:.2f}s | Runs: {test['total_runs']}")
            print()

    # Trends summary
    if trends:
        recent_trend = trends[-7:] if len(trends) >= 7 else trends
        avg_success = (
            sum(t["success_rate"] for t in recent_trend) / len(recent_trend)
        )
        print(f"📈 RECENT TREND (Last {len(recent_trend)} days)\n")
        print(f"  Average Success Rate: {avg_success:.1f}%")
        if avg_success >= 95:
            print(f"  Status: ✅ Excellent")
        elif avg_success >= 80:
            print(f"  Status: ⚠️  Good (some failures)")
        else:
            print(f"  Status: ❌ Needs attention")
        print()

    print(f"{'=' * 70}\n")


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "report":
        return handle_report_command(args)
    elif args.command == "analyze":
        return handle_analyze_command(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
