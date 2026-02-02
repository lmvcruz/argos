"""
Scout CLI - Command-line interface for CI/CD inspection and analysis.

This module provides the main CLI entry point and command handlers for Scout,
integrating all core components (providers, log retrieval, parsing, analysis, reporting).
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from scout import __version__
from scout.analysis import AnalysisEngine
from scout.failure_parser import FailureParser
from scout.log_retrieval import LogRetriever
from scout.providers.github_actions import GitHubActionsProvider
from scout.reporting import ConsoleReporter, CsvExporter, HtmlReporter, JsonExporter


class Config:
    """Configuration manager for Scout CLI."""

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file or Path.home() / ".scout" / "config.json"
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """
        Load configuration from file.

        Returns:
            Configuration dictionary
        """
        if self.config_file.exists():
            import json

            with open(self.config_file, "r") as f:
                return json.load(f)
        return {}

    def get(self, key: str, default=None):
        """
        Get configuration value.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: str):
        """
        Set configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Configuration value
        """
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_config()

    def get_all(self) -> dict:
        """
        Get all configuration values.

        Returns:
            Complete configuration dictionary
        """
        return self.config

    def _save_config(self):
        """Save configuration to file."""
        import json

        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="scout",
        description="Scout - CI/CD inspection and failure analysis tool",
        epilog="For more information, visit https://github.com/lmvcruz/argos",
    )

    parser.add_argument("--version", action="version", version=f"Scout {__version__}")

    # Create parent parser for common options
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--token",
        help="GitHub personal access token (or use GITHUB_TOKEN env var)",
    )
    parent_parser.add_argument(
        "--repo",
        help="GitHub repository in owner/repo format (or use GITHUB_REPO env var)",
    )
    parent_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parent_parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress non-error output"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # 'logs' command
    logs_parser = subparsers.add_parser(
        "logs", help="Retrieve CI logs for a workflow", parents=[parent_parser]
    )
    logs_parser.add_argument("workflow", help="Workflow name")
    logs_parser.add_argument(
        "--limit", type=int, default=10, help="Number of runs to retrieve (default: 10)"
    )
    logs_parser.add_argument("--branch", help="Filter by branch name")
    logs_parser.add_argument("--output", help="Output directory for logs")

    # 'analyze' command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze test failures for a specific run", parents=[parent_parser]
    )
    analyze_parser.add_argument("run_id", help="Workflow run ID")
    analyze_parser.add_argument(
        "--format",
        choices=["console", "html", "json", "csv"],
        default="console",
        help="Output format (default: console)",
    )
    analyze_parser.add_argument("--output", help="Output file path (for HTML/JSON/CSV formats)")

    # 'trends' command
    trends_parser = subparsers.add_parser(
        "trends", help="Analyze failure trends over time", parents=[parent_parser]
    )
    trends_parser.add_argument("workflow", help="Workflow name")
    trends_parser.add_argument(
        "--days", type=int, default=7, help="Number of days to analyze (default: 7)"
    )
    trends_parser.add_argument(
        "--format",
        choices=["console", "html", "json", "csv"],
        default="console",
        help="Output format (default: console)",
    )

    # 'flaky' command
    flaky_parser = subparsers.add_parser(
        "flaky", help="Detect flaky tests", parents=[parent_parser]
    )
    flaky_parser.add_argument(
        "--threshold",
        type=float,
        default=0.2,
        help="Flakiness threshold (0.0-1.0, default: 0.2)",
    )
    flaky_parser.add_argument(
        "--min-runs",
        type=int,
        default=5,
        help="Minimum runs to consider (default: 5)",
    )
    flaky_parser.add_argument(
        "--format",
        choices=["console", "html", "json", "csv"],
        default="console",
        help="Output format (default: console)",
    )

    # 'config' command
    config_parser = subparsers.add_parser("config", help="Manage Scout configuration")
    config_subparsers = config_parser.add_subparsers(
        dest="config_command", help="Configuration commands"
    )

    # 'config show'
    config_subparsers.add_parser("show", help="Show current configuration")

    # 'config get'
    config_get_parser = config_subparsers.add_parser("get", help="Get configuration value")
    config_get_parser.add_argument("key", help="Configuration key")

    # 'config set'
    config_set_parser = config_subparsers.add_parser("set", help="Set configuration value")
    config_set_parser.add_argument("key", help="Configuration key")
    config_set_parser.add_argument("value", help="Configuration value")

    return parser


def get_github_credentials(args) -> tuple[str, str, Optional[str]]:
    """
    Get GitHub credentials from arguments or environment.

    Args:
        args: Parsed command-line arguments

    Returns:
        Tuple of (owner, repo, token)

    Raises:
        ValueError: If required credentials are missing or invalid
    """
    # Get token
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError(
            "GitHub token required. Provide via --token option or "
            "GITHUB_TOKEN environment variable."
        )

    # Get repository
    repo = args.repo or os.environ.get("GITHUB_REPO")
    if not repo:
        raise ValueError(
            "GitHub repository required. Provide via --repo option or "
            "GITHUB_REPO environment variable (format: owner/repo)."
        )

    # Parse owner/repo
    parts = repo.split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid repository format: {repo}. Expected format: owner/repo")

    owner, repo_name = parts
    return owner, repo_name, token


def handle_logs_command(args) -> int:
    """
    Handle the 'logs' command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        owner, repo, token = get_github_credentials(args)

        # Initialize provider and retriever
        provider = GitHubActionsProvider(owner=owner, repo=repo, token=token)
        retriever = LogRetriever(provider=provider)

        # Retrieve logs
        if not args.quiet:
            print(f"Retrieving logs for workflow '{args.workflow}'...")

        logs = retriever.retrieve_logs(
            workflow=args.workflow,
            limit=args.limit,
            branch=args.branch,
            output_dir=args.output,
        )

        if not args.quiet:
            print(f"✓ Retrieved {len(logs)} workflow run(s)")
            if args.output:
                print(f"✓ Logs saved to {args.output}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_analyze_command(args) -> int:
    """
    Handle the 'analyze' command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        owner, repo, token = get_github_credentials(args)

        # Initialize components
        provider = GitHubActionsProvider(owner=owner, repo=repo, token=token)
        retriever = LogRetriever(provider=provider)
        parser = FailureParser()
        engine = AnalysisEngine()

        # Get logs
        if not args.quiet:
            print(f"Retrieving logs for run {args.run_id}...")

        logs = retriever.get_logs(run_id=args.run_id)

        # Parse failures
        if not args.quiet:
            print("Parsing test failures...")

        failures = parser.parse(logs)

        # Analyze failures
        if not args.quiet:
            print("Analyzing failures...")

        analysis = engine.analyze(failures)

        # Generate report
        if args.format == "console":
            reporter = ConsoleReporter()
            report = reporter.generate_report(analysis)
            print(report)

        elif args.format == "html":
            reporter = HtmlReporter()
            report = reporter.generate_report(analysis)
            if args.output:
                reporter.save(report, args.output)
                if not args.quiet:
                    print(f"✓ HTML report saved to {args.output}")
            else:
                print(report)

        elif args.format == "json":
            exporter = JsonExporter()
            report = exporter.export(analysis)
            if args.output:
                exporter.save(report, args.output)
                if not args.quiet:
                    print(f"✓ JSON report saved to {args.output}")
            else:
                print(report)

        elif args.format == "csv":
            exporter = CsvExporter()
            report = exporter.export(analysis)
            if args.output:
                exporter.save(report, args.output)
                if not args.quiet:
                    print(f"✓ CSV report saved to {args.output}")
            else:
                print(report)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_trends_command(args) -> int:
    """
    Handle the 'trends' command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        owner, repo, token = get_github_credentials(args)

        # Initialize components
        provider = GitHubActionsProvider(owner=owner, repo=repo, token=token)
        retriever = LogRetriever(provider=provider)
        # Analysis engine for future use
        # engine = AnalysisEngine()

        # Retrieve logs for the specified period
        if not args.quiet:
            print(f"Analyzing trends for '{args.workflow}' over {args.days} days...")

        logs = retriever.retrieve_logs(workflow=args.workflow, days=args.days)

        # Analyze trends (for future use)
        # trends = engine.analyze_trends(logs)

        # Generate report
        if args.format == "console":
            # For now, just print a summary (trends analysis not fully implemented yet)
            print(f"\nTrend Analysis for '{args.workflow}'")
            print(f"Analyzed {len(logs)} runs")
            print("\nNote: Full trend visualization coming soon")

        elif args.format == "json":
            exporter = JsonExporter()
            report = exporter.export({"workflow": args.workflow, "logs": len(logs)})
            print(report)

        elif args.format == "csv":
            # Simplified for now
            print("workflow,log_count")
            print(f"{args.workflow},{len(logs)}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_flaky_command(args) -> int:
    """
    Handle the 'flaky' command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Initialize analysis engine
        engine = AnalysisEngine()

        # Detect flaky tests
        if not args.quiet:
            print(
                f"Detecting flaky tests (threshold: {args.threshold}, min runs: {args.min_runs})..."
            )

        flaky_tests = engine.detect_flaky_tests(threshold=args.threshold, min_runs=args.min_runs)

        # Generate report
        if args.format == "console":
            reporter = ConsoleReporter()
            report = reporter.generate_flaky_test_report(flaky_tests)
            print(report)

        elif args.format == "json":
            exporter = JsonExporter()
            report = exporter.export({"flaky_tests": flaky_tests})
            print(report)

        elif args.format == "csv":
            # Simplified CSV output for flaky tests
            print("test_name,pass_rate,fail_rate,total_runs")
            for test in flaky_tests:
                print(f"{test.test_name},{test.pass_rate},{test.fail_rate},{test.total_runs}")

        if not args.quiet:
            print(f"\n✓ Found {len(flaky_tests)} flaky test(s)")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_config_command(args) -> int:
    """
    Handle the 'config' command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        config = Config()

        if args.config_command == "show":
            # Show all configuration
            import json

            print(json.dumps(config.get_all(), indent=2))

        elif args.config_command == "get":
            # Get specific configuration value
            value = config.get(args.key)
            if value is not None:
                print(value)
            else:
                print(f"Configuration key '{args.key}' not found", file=sys.stderr)
                return 1

        elif args.config_command == "set":
            # Set configuration value
            config.set(args.key, args.value)
            if not args.quiet:
                print(f"✓ Set {args.key} = {args.value}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def main(argv=None) -> int:
    """
    Main entry point for Scout CLI.

    Args:
        argv: Command-line arguments (uses sys.argv if None)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()

    # Parse arguments
    try:
        if argv is None:
            args = parser.parse_args()
        else:
            args = parser.parse_args(argv[1:] if isinstance(argv, list) else argv)
    except SystemExit as e:
        # argparse raises SystemExit on parse errors or --help
        return e.code if e.code is not None else 0

    # Check if command was provided
    if not hasattr(args, "command") or args.command is None:
        parser.print_help()
        return 1

    # Route to appropriate command handler
    try:
        if args.command == "logs":
            return handle_logs_command(args)
        elif args.command == "analyze":
            return handle_analyze_command(args)
        elif args.command == "trends":
            return handle_trends_command(args)
        elif args.command == "flaky":
            return handle_flaky_command(args)
        elif args.command == "config":
            return handle_config_command(args)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130  # Standard exit code for SIGINT


if __name__ == "__main__":
    sys.exit(main())
