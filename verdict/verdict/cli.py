"""
Command-line interface for Verdict.

This module provides the CLI for running tests and viewing results.
"""

import argparse
import sys
from pathlib import Path

from verdict.logger import TestLogger
from verdict.runner import TestRunner


def main() -> int:
    """
    Main entry point for Verdict CLI.

    Returns:
        Exit code (0 for success, 1 for failures, 2 for errors)
    """
    parser = argparse.ArgumentParser(
        description="Verdict: Generic test validation framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  verdict run --config config.yaml
  verdict run --config config.yaml --case scout_ci_github_actions_client
  verdict run --config config.yaml --workers 8
  verdict run --config config.yaml --format json
  verdict run --config config.yaml --no-color
        """,
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run test validation")
    run_parser.add_argument(
        "--config",
        "-c",
        type=str,
        required=True,
        help="Path to configuration YAML file",
    )
    run_parser.add_argument(
        "--case",
        type=str,
        default=None,
        help="Run specific test suite or case by name",
    )
    run_parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=None,
        help="Maximum number of parallel workers (default: from config or CPU count)",
    )
    run_parser.add_argument(
        "--format",
        "-f",
        choices=["console", "json"],
        default="console",
        help="Output format (default: console)",
    )
    run_parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    # Parse arguments
    args = parser.parse_args()

    # Check if command was provided
    if not args.command:
        parser.print_help()
        return 2

    # Execute command
    if args.command == "run":
        return run_tests(args)

    return 0


def run_tests(args: argparse.Namespace) -> int:
    """
    Run tests based on command-line arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failures, 2 for errors)
    """
    config_path = Path(args.config)

    # Verify config file exists
    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}", file=sys.stderr)
        return 2

    try:
        # Create runner and execute tests
        runner = TestRunner(config_path)
        results = runner.run_all(max_workers=args.workers, case_filter=args.case)

        # Check if a filter was applied and no results were found
        if args.case and not results:
            print(f"Warning: No test cases found matching '{args.case}'", file=sys.stderr)

        # Create logger and output results
        use_color = not args.no_color
        logger = TestLogger(use_color=use_color)

        if args.format == "json":
            json_output = logger.log_json(results)
            print(json_output)
        else:
            logger.log_console(results)

        # Determine exit code
        # Exit code 2: Execution errors (e.g., import failures, runtime errors)
        # Exit code 1: Test failures (validation failures)
        # Exit code 0: All tests passed (or no tests ran due to filter)
        error_count = sum(1 for r in results if r.error is not None)
        if error_count > 0:
            return 2

        failed_count = sum(1 for r in results if not r.passed)
        if failed_count > 0:
            return 1

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
