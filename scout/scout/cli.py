"""
Scout CLI - Command-line interface for CI/CD inspection and analysis.

This module provides the main CLI entry point and command handlers for Scout,
integrating all core components (providers, log retrieval, parsing, analysis, reporting).
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

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

    def _load_config(self) -> Dict:
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

    def get_all(self) -> Dict:
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

    # 'ci' command (Phase 0.1.4: CI data collection and analysis)
    setup_ci_parser(subparsers)

    return parser


def get_github_credentials(args) -> Tuple[str, str, Optional[str]]:
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
        elif args.command == "ci":
            return handle_ci_command(args)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130  # Standard exit code for SIGINT


# ============================================================================
# CI Commands (Phase 0.1.4)
# ============================================================================


def setup_ci_parser(subparsers):
    """
    Set up the 'ci' command and its subcommands.

    Args:
        subparsers: The subparsers object from ArgumentParser

    Returns:
        The ci parser object
    """
    # Create parent parser for common CI options
    ci_parent = subparsers._parser_class(add_help=False)
    ci_parent.add_argument(
        "--token",
        help="GitHub personal access token (or use GITHUB_TOKEN env var)",
    )
    ci_parent.add_argument(
        "--repo",
        help="GitHub repository in owner/repo format (or use GITHUB_REPO env var)",
    )
    ci_parent.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    ci_parent.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress non-error output"
    )
    ci_parent.add_argument(
        "--db",
        default="scout.db",
        help="Path to Scout database (default: scout.db)",
    )

    # Main 'ci' command
    ci_parser = subparsers.add_parser(
        "ci",
        help="CI data collection and analysis commands",
        description="Fetch, download, and analyze CI workflow data from GitHub Actions",
    )

    # Create subcommands for ci
    ci_subparsers = ci_parser.add_subparsers(
        dest="ci_command", help="CI subcommands", required=True
    )

    # 'ci fetch' subcommand
    fetch_parser = ci_subparsers.add_parser(
        "fetch",
        help="Fetch CI workflow runs from GitHub Actions",
        parents=[ci_parent],
    )
    fetch_parser.add_argument("--workflow", required=True, help="Workflow name to fetch")
    fetch_parser.add_argument(
        "--limit", type=int, default=50, help="Maximum number of runs to fetch (default: 50)"
    )
    fetch_parser.add_argument("--branch", help="Filter by branch name")
    fetch_parser.add_argument(
        "--with-jobs",
        action="store_true",
        help="Also fetch jobs for each workflow run",
    )

    # 'ci download' subcommand
    download_parser = ci_subparsers.add_parser(
        "download",
        help="Download logs for a specific workflow run",
        parents=[ci_parent],
    )
    download_parser.add_argument("--run-id", type=int, required=True, help="Workflow run ID")
    download_parser.add_argument(
        "--output",
        default="./ci-logs",
        help="Output directory for logs (default: ./ci-logs)",
    )
    download_parser.add_argument(
        "--parse",
        action="store_true",
        help="Parse logs and store test results in database",
    )

    # 'ci analyze' subcommand
    analyze_parser = ci_subparsers.add_parser(
        "analyze",
        help="Analyze CI failures and patterns",
        parents=[ci_parent],
    )
    analyze_parser.add_argument(
        "--window",
        type=int,
        default=30,
        help="Time window in days for analysis (default: 30)",
    )
    analyze_parser.add_argument(
        "--runner-os",
        choices=["ubuntu-latest", "windows-latest", "macos-latest", "all"],
        default="all",
        help="Filter by runner OS (default: all)",
    )
    analyze_parser.add_argument(
        "--workflow",
        help="Filter by workflow name",
    )
    analyze_parser.add_argument(
        "--format",
        choices=["console", "json", "csv"],
        default="console",
        help="Output format (default: console)",
    )
    analyze_parser.add_argument(
        "--output-file",
        help="Save output to file",
    )

    # 'ci compare' subcommand
    compare_parser = ci_subparsers.add_parser(
        "compare",
        help="Compare local vs CI test results",
        parents=[ci_parent],
    )
    compare_parser.add_argument(
        "--local-run",
        required=True,
        help="Local execution ID",
    )
    compare_parser.add_argument(
        "--ci-run",
        type=int,
        required=True,
        help="CI workflow run ID",
    )
    compare_parser.add_argument(
        "--format",
        choices=["console", "json"],
        default="console",
        help="Output format (default: console)",
    )

    # 'ci patterns' subcommand
    patterns_parser = ci_subparsers.add_parser(
        "patterns",
        help="Show identified failure patterns",
        parents=[ci_parent],
    )
    patterns_parser.add_argument(
        "--type",
        choices=["timeout", "platform-specific", "setup", "dependency", "all"],
        default="all",
        help="Pattern type to show (default: all)",
    )
    patterns_parser.add_argument(
        "--window",
        type=int,
        default=30,
        help="Time window in days (default: 30)",
    )
    patterns_parser.add_argument(
        "--min-count",
        type=int,
        default=1,
        help="Minimum occurrence count (default: 1)",
    )

    # 'ci show' subcommand
    show_parser = ci_subparsers.add_parser(
        "show",
        help="Show details of a specific workflow run or job",
        parents=[ci_parent],
    )
    show_parser.add_argument(
        "--run-id",
        type=int,
        help="Workflow run ID (GitHub's unique identifier)",
    )
    show_parser.add_argument(
        "--workflow",
        help="Workflow name (required if using --run-number)",
    )
    show_parser.add_argument(
        "--run-number",
        type=int,
        help="Workflow run number (e.g., #70)",
    )
    show_parser.add_argument(
        "--job-id",
        type=int,
        help="Show details of a specific job (use with --run-id)",
    )
    show_parser.add_argument(
        "--group-by",
        choices=["status", "platform", "none"],
        default="status",
        help="How to group jobs (default: status)",
    )

    # 'ci sync' subcommand
    sync_parser = ci_subparsers.add_parser(
        "sync",
        help="Sync CI data to Anvil validation history",
        parents=[ci_parent],
    )
    sync_parser.add_argument(
        "--anvil-db",
        default="anvil_stats.db",
        help="Path to Anvil database (default: anvil_stats.db)",
    )
    sync_parser.add_argument(
        "--run-id",
        type=int,
        help="Sync specific run ID (if not provided, syncs recent runs)",
    )
    sync_parser.add_argument(
        "--workflow",
        help="Filter by workflow name",
    )
    sync_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of recent runs to sync (default: 10)",
    )

    # 'ci anvil-compare' subcommand
    anvil_compare_parser = ci_subparsers.add_parser(
        "anvil-compare",
        help="Compare local (Anvil) vs CI test results",
        parents=[ci_parent],
    )
    anvil_compare_parser.add_argument(
        "--anvil-db",
        default="anvil_stats.db",
        help="Path to Anvil database (default: anvil_stats.db)",
    )
    anvil_compare_parser.add_argument(
        "--local-run",
        type=int,
        required=True,
        help="Anvil validation run ID (local execution)",
    )
    anvil_compare_parser.add_argument(
        "--ci-run",
        type=int,
        required=True,
        help="Scout workflow run ID (CI execution)",
    )

    # 'ci ci-failures' subcommand
    ci_failures_parser = ci_subparsers.add_parser(
        "ci-failures",
        help="Identify tests that fail only in CI",
        parents=[ci_parent],
    )
    ci_failures_parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Look back this many days (default: 30)",
    )
    ci_failures_parser.add_argument(
        "--min-failures",
        type=int,
        default=2,
        help="Minimum CI failures to report (default: 2)",
    )

    return ci_parser


def get_ci_github_client(args):
    """
    Create GitHub Actions client from arguments for CI commands.

    Args:
        args: Parsed command-line arguments

    Returns:
        GitHubActionsClient instance

    Raises:
        ValueError: If required credentials are missing
    """
    from scout.ci.github_actions_client import GitHubActionsClient
    from scout.storage import DatabaseManager

    # Get token
    token = getattr(args, "token", None) or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError(
            "GitHub token required. Provide via --token option or "
            "GITHUB_TOKEN environment variable."
        )

    # Get repository
    repo = getattr(args, "repo", None) or os.environ.get("GITHUB_REPO")
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

    # Initialize provider and database
    provider = GitHubActionsProvider(owner=owner, repo=repo_name, token=token)
    db_manager = DatabaseManager(db_path=args.db)
    db_manager.initialize()

    return GitHubActionsClient(provider=provider, db_manager=db_manager)


def handle_ci_fetch_command(args) -> int:
    """
    Handle 'ci fetch' command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        client = get_ci_github_client(args)

        if not args.quiet:
            print(f"Fetching workflow runs for '{args.workflow}'...")

        # Fetch workflow runs
        runs = client.fetch_workflow_runs(workflow=args.workflow, limit=args.limit)

        if not args.quiet:
            print(f"✓ Fetched {len(runs)} workflow run(s)")

        # Show fetched runs
        if not args.quiet and runs:
            print("\nRuns fetched:")
            for run in runs:
                status_icon = "✓" if run.conclusion == "success" else "✗"
                print(f"  {status_icon} #{run.run_id} ({run.status}/{run.conclusion}) - {run.started_at}")

        # Optionally fetch jobs
        total_jobs = 0
        if args.with_jobs:
            if not args.quiet:
                print("\nFetching jobs for each run...")

            for run in runs:
                jobs = client.fetch_workflow_jobs(run_id=run.run_id)
                total_jobs += len(jobs)

            if not args.quiet:
                print(f"✓ Fetched {total_jobs} job(s)")

        # Print summary and next steps
        if not args.quiet:
            print("\nSummary:")
            print(f"  Workflow: {args.workflow}")
            print(f"  Runs: {len(runs)}")
            if args.with_jobs:
                print(f"  Jobs: {total_jobs}")
            print(f"  Database: {args.db}")

            if runs:
                print("\nNext steps:")
                print(f"  View details: scout ci show --run-id {runs[0].run_id}")
                print(f"  Analyze trends: scout ci analyze --window 7")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_ci_download_command(args) -> int:
    """
    Handle 'ci download' command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        from scout.parsers.ci_log_parser import CILogParser

        client = get_ci_github_client(args)

        if not args.quiet:
            print(f"Downloading logs for run {args.run_id}...")

        # Create output directory
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Fetch jobs for the run
        jobs = client.fetch_workflow_jobs(run_id=args.run_id)

        if not jobs:
            print(f"No jobs found for run {args.run_id}", file=sys.stderr)
            return 1

        # Download logs for each job
        downloaded_count = 0
        parsed_count = 0

        for job in jobs:
            if not args.quiet:
                print(f"  Downloading logs for job {job.job_name}...")

            # Download log (placeholder - full implementation needed)
            log_path = output_dir / f"job-{job.job_id}.log"
            log_path.write_text(f"# Logs for job {job.job_id}\n# {job.job_name}\n")
            downloaded_count += 1

            # Optionally parse logs
            if args.parse:
                parser = CILogParser()
                log_content = log_path.read_text()

                # Parse test results
                test_results = parser.parse_pytest_log(log_content)
                parsed_count += len(test_results)

        if not args.quiet:
            print(f"\n✓ Downloaded {downloaded_count} log file(s) to {output_dir}")
            if args.parse:
                print(f"✓ Parsed {parsed_count} test result(s)")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_ci_analyze_command(args) -> int:
    """
    Handle 'ci analyze' command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        from datetime import datetime, timedelta

        from scout.storage import DatabaseManager, WorkflowJob, WorkflowRun

        # Initialize database
        db_manager = DatabaseManager(db_path=args.db)
        db_manager.initialize()
        session = db_manager.get_session()

        if not args.quiet:
            print(f"Analyzing CI failures (window: {args.window} days)...")

        # Calculate time window
        cutoff_date = datetime.utcnow() - timedelta(days=args.window)

        # Query workflow runs
        query = session.query(WorkflowRun).filter(WorkflowRun.started_at >= cutoff_date)

        if args.workflow:
            query = query.filter(WorkflowRun.workflow_name == args.workflow)

        runs = query.all()

        # Analyze runs
        total_runs = len(runs)
        failed_runs = sum(1 for r in runs if r.conclusion == "failure")
        success_runs = sum(1 for r in runs if r.conclusion == "success")
        success_rate = (success_runs / total_runs * 100) if total_runs > 0 else 0

        # Group by runner OS if jobs are available
        os_stats = {}
        for run in runs:
            jobs = session.query(WorkflowJob).filter(WorkflowJob.run_id == run.run_id).all()
            for job in jobs:
                if args.runner_os != "all" and job.runner_os != args.runner_os:
                    continue

                os = job.runner_os or "unknown"
                if os not in os_stats:
                    os_stats[os] = {"total": 0, "failed": 0, "success": 0}

                os_stats[os]["total"] += 1
                if job.conclusion == "failure":
                    os_stats[os]["failed"] += 1
                elif job.conclusion == "success":
                    os_stats[os]["success"] += 1

        # Generate output
        if args.format == "console":
            print("\n" + "=" * 60)
            print("CI FAILURE ANALYSIS")
            print("=" * 60)
            print(f"\nTime Window: {args.window} days")
            if args.workflow:
                print(f"Workflow: {args.workflow}")
            print(f"\nOverall Statistics:")
            print(f"  Total Runs: {total_runs}")
            print(f"  Successful: {success_runs} ({success_rate:.1f}%)")
            print(f"  Failed: {failed_runs}")

            if os_stats:
                print(f"\nBy Runner OS:")
                for os, stats in sorted(os_stats.items()):
                    total = stats["total"]
                    failed = stats["failed"]
                    success = stats["success"]
                    rate = (success / total * 100) if total > 0 else 0
                    print(f"  {os}:")
                    print(f"    Total: {total}")
                    print(f"    Success: {success} ({rate:.1f}%)")
                    print(f"    Failed: {failed}")

        elif args.format == "json":
            import json

            result = {
                "window_days": args.window,
                "workflow": args.workflow,
                "total_runs": total_runs,
                "successful_runs": success_runs,
                "failed_runs": failed_runs,
                "success_rate": round(success_rate, 2),
                "by_runner_os": os_stats,
            }
            output = json.dumps(result, indent=2)
            if args.output_file:
                Path(args.output_file).write_text(output)
                if not args.quiet:
                    print(f"✓ Analysis saved to {args.output_file}")
            else:
                print(output)

        elif args.format == "csv":
            # Simple CSV format
            lines = ["runner_os,total,success,failed,success_rate"]
            for os, stats in sorted(os_stats.items()):
                total = stats["total"]
                success = stats["success"]
                failed = stats["failed"]
                rate = (success / total * 100) if total > 0 else 0
                lines.append(f"{os},{total},{success},{failed},{rate:.2f}")

            output = "\n".join(lines)
            if args.output_file:
                Path(args.output_file).write_text(output)
                if not args.quiet:
                    print(f"✓ Analysis saved to {args.output_file}")
            else:
                print(output)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_ci_compare_command(args) -> int:
    """
    Handle 'ci compare' command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        import json

        from scout.storage import DatabaseManager, WorkflowJob, WorkflowTestResult

        # Initialize database
        db_manager = DatabaseManager(db_path=args.db)
        db_manager.initialize()
        session = db_manager.get_session()

        if not args.quiet:
            print(f"Comparing local run '{args.local_run}' with CI run {args.ci_run}...")

        # Query CI test results
        jobs = session.query(WorkflowJob).filter(WorkflowJob.run_id == args.ci_run).all()

        if not jobs:
            print(f"No jobs found for CI run {args.ci_run}", file=sys.stderr)
            return 1

        ci_tests = {}
        for job in jobs:
            tests = (
                session.query(WorkflowTestResult)
                .filter(WorkflowTestResult.job_id == job.job_id)
                .all()
            )
            for test in tests:
                ci_tests[test.test_nodeid] = {
                    "outcome": test.outcome,
                    "runner_os": test.runner_os,
                    "python_version": test.python_version,
                    "duration": test.duration,
                }

        # Generate output
        if args.format == "console":
            print("\n" + "=" * 60)
            print("LOCAL VS CI COMPARISON")
            print("=" * 60)
            print(f"\nLocal Run: {args.local_run}")
            print(f"CI Run: {args.ci_run}")
            print(f"\nCI Test Results: {len(ci_tests)}")

            # Group by outcome
            passed = sum(1 for t in ci_tests.values() if t["outcome"] == "passed")
            failed = sum(1 for t in ci_tests.values() if t["outcome"] == "failed")
            skipped = sum(1 for t in ci_tests.values() if t["outcome"] == "skipped")

            print(f"  Passed: {passed}")
            print(f"  Failed: {failed}")
            print(f"  Skipped: {skipped}")

            print("\nNote: Full local/CI comparison requires Anvil integration (Phase 0.3)")

        elif args.format == "json":
            result = {
                "local_run": args.local_run,
                "ci_run": args.ci_run,
                "ci_test_count": len(ci_tests),
                "ci_tests": ci_tests,
            }
            print(json.dumps(result, indent=2))

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_ci_patterns_command(args) -> int:
    """
    Handle 'ci patterns' command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        from datetime import datetime, timedelta

        from scout.parsers.ci_log_parser import CILogParser
        from scout.storage import DatabaseManager, WorkflowTestResult

        # Initialize database
        db_manager = DatabaseManager(db_path=args.db)
        db_manager.initialize()
        session = db_manager.get_session()

        if not args.quiet:
            print(f"Identifying failure patterns (window: {args.window} days)...")

        # Calculate time window
        cutoff_date = datetime.utcnow() - timedelta(days=args.window)

        # Query test results with failures
        query = (
            session.query(WorkflowTestResult)
            .filter(WorkflowTestResult.timestamp >= cutoff_date)
            .filter(WorkflowTestResult.outcome == "failed")
        )

        failed_tests = query.all()

        # Analyze patterns using CILogParser
        parser = CILogParser()
        patterns_by_type = {
            "timeout": [],
            "platform-specific": [],
            "setup": [],
            "dependency": [],
        }

        # Group failures by test
        test_failures = {}
        for test in failed_tests:
            nodeid = test.test_nodeid
            if nodeid not in test_failures:
                test_failures[nodeid] = []
            test_failures[nodeid].append(test)

        # Detect patterns from error messages
        for nodeid, failures in test_failures.items():
            if len(failures) < args.min_count:
                continue

            # Analyze error messages for patterns
            for failure in failures:
                if failure.error_message:
                    patterns = parser.detect_failure_patterns(failure.error_message)
                    for pattern in patterns:
                        if args.type == "all" or pattern["type"] == args.type:
                            pattern["test_nodeid"] = nodeid
                            pattern["occurrences"] = len(failures)
                            patterns_by_type[pattern["type"]].append(pattern)

        # Print results
        total_patterns = sum(len(p) for p in patterns_by_type.values())

        print("\n" + "=" * 60)
        print("FAILURE PATTERNS")
        print("=" * 60)
        print(f"\nTime Window: {args.window} days")
        print(f"Pattern Type: {args.type}")
        print(f"Total Patterns: {total_patterns}\n")

        for pattern_type, patterns in patterns_by_type.items():
            if not patterns:
                continue

            print(f"\n{pattern_type.upper()} ({len(patterns)} patterns)")
            print("-" * 60)

            for i, pattern in enumerate(patterns[:10], 1):  # Show top 10
                print(f"\n{i}. {pattern['description']}")
                print(f"   Test: {pattern.get('test_nodeid', 'N/A')}")
                print(f"   Occurrences: {pattern['occurrences']}")
                if pattern.get("suggested_fix"):
                    print(f"   Fix: {pattern['suggested_fix']}")

        if not total_patterns:
            print("No failure patterns found in the specified time window.")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_ci_show_command(args) -> int:
    """
    Handle 'ci show' command to display details of a specific workflow run or job.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        from scout.storage import DatabaseManager
        from scout.storage.schema import WorkflowRun, WorkflowJob
        from collections import defaultdict

        # Connect to database
        db = DatabaseManager(args.db)
        db.initialize()
        session = db.get_session()

        # If showing a specific job
        if args.job_id:
            from scout.storage.schema import WorkflowTestResult

            job = session.query(WorkflowJob).filter_by(job_id=args.job_id).first()
            if not job:
                print(f"Error: Job not found: {args.job_id}", file=sys.stderr)
                session.close()
                return 1

            # Display job details
            icon = "✓" if job.conclusion == "success" else "✗"
            print(f"\n{icon} Job: {job.job_name}")
            print(f"Job ID: {job.job_id}")
            print(f"Run ID: {job.run_id}")
            print(f"Status: {job.status}/{job.conclusion}")
            if job.runner_os:
                print(f"Runner: {job.runner_os}")
            if job.python_version:
                print(f"Python: {job.python_version}")

            if job.duration_seconds:
                minutes = job.duration_seconds // 60
                seconds = job.duration_seconds % 60
                print(f"Duration: {job.duration_seconds}s ({minutes}m {seconds}s)")

            if job.started_at:
                print(f"Started: {job.started_at}")
            if job.completed_at:
                print(f"Completed: {job.completed_at}")

            # Display test results if available
            test_results = (
                session.query(WorkflowTestResult)
                .filter_by(job_id=args.job_id)
                .order_by(WorkflowTestResult.outcome, WorkflowTestResult.test_nodeid)
                .all()
            )

            if test_results:
                # Group by outcome
                by_outcome = defaultdict(list)
                for result in test_results:
                    by_outcome[result.outcome].append(result)

                print(f"\nTest Results ({len(test_results)} tests):")

                # Show failed tests first with details
                if "failed" in by_outcome:
                    failed = by_outcome["failed"]
                    print(f"\n  Failed ({len(failed)}):")
                    for result in failed:
                        duration_str = f" - {result.duration:.2f}s" if result.duration else ""
                        print(f"    ✗ {result.test_nodeid}{duration_str}")
                        if result.error_message:
                            # Show first line of error message
                            first_line = result.error_message.split("\n")[0]
                            print(f"      Error: {first_line}")
                        if result.error_traceback and args.verbose:
                            # Show full traceback in verbose mode
                            print(f"      Traceback:")
                            for line in result.error_traceback.split("\n")[:10]:  # First 10 lines
                                print(f"        {line}")
                            if len(result.error_traceback.split("\n")) > 10:
                                print(f"        ... (use --verbose for full traceback)")

                # Show error tests
                if "error" in by_outcome:
                    errors = by_outcome["error"]
                    print(f"\n  Errors ({len(errors)}):")
                    for result in errors:
                        duration_str = f" - {result.duration:.2f}s" if result.duration else ""
                        print(f"    ⚠ {result.test_nodeid}{duration_str}")
                        if result.error_message:
                            first_line = result.error_message.split("\n")[0]
                            print(f"      Error: {first_line}")

                # Show passed tests (compact)
                if "passed" in by_outcome:
                    passed = by_outcome["passed"]
                    print(f"\n  Passed ({len(passed)}):")
                    if len(passed) <= 10 or args.verbose:
                        for result in passed:
                            duration_str = f" - {result.duration:.2f}s" if result.duration else ""
                            print(f"    ✓ {result.test_nodeid}{duration_str}")
                    else:
                        # Show first few and summary
                        for result in passed[:5]:
                            duration_str = f" - {result.duration:.2f}s" if result.duration else ""
                            print(f"    ✓ {result.test_nodeid}{duration_str}")
                        print(f"    ... and {len(passed) - 5} more (use --verbose to see all)")

                # Show skipped tests (compact)
                if "skipped" in by_outcome:
                    skipped = by_outcome["skipped"]
                    print(f"\n  Skipped ({len(skipped)}):")
                    if args.verbose:
                        for result in skipped:
                            print(f"    - {result.test_nodeid}")
                    else:
                        print(f"    (use --verbose to see details)")

                # Summary
                print("\nSummary:")
                if "passed" in by_outcome:
                    print(f"  Passed: {len(by_outcome['passed'])}")
                if "failed" in by_outcome:
                    print(f"  Failed: {len(by_outcome['failed'])}")
                if "error" in by_outcome:
                    print(f"  Errors: {len(by_outcome['error'])}")
                if "skipped" in by_outcome:
                    print(f"  Skipped: {len(by_outcome['skipped'])}")

            else:
                print("\nNo test results found for this job.")
                print("Test results may not have been parsed yet.")
                if job.logs_url:
                    print(f"\nDownload logs:")
                    print(f"  scout ci download --run-id {job.run_id}")

            print(f"\nView run: scout ci show --run-id {job.run_id}")
            session.close()
            return 0

        # Validate arguments for run display
        if not args.run_id and not (args.workflow and args.run_number):
            print(
                "Error: Must provide either --run-id or --job-id",
                file=sys.stderr,
            )
            return 1

        # Query workflow run
        if args.run_id:
            run = session.query(WorkflowRun).filter_by(run_id=args.run_id).first()
        else:
            print(
                "Error: --workflow and --run-number not yet implemented. Please use --run-id.",
                file=sys.stderr,
            )
            session.close()
            return 1

        if not run:
            print(f"Error: Run not found in database: {args.run_id}", file=sys.stderr)
            print("\nTry fetching it first:")
            print(f"  scout ci fetch --workflow 'Workflow Name' --limit 10 --with-jobs")
            session.close()
            return 1

        # Query jobs for this run
        jobs = session.query(WorkflowJob).filter_by(run_id=run.run_id).all()

        # Display run details
        status_icon = "✓" if run.conclusion == "success" else "✗"
        print(f"\n{status_icon} Workflow Run: {run.workflow_name} #{run.run_id}")
        print(f"Status: {run.status}/{run.conclusion}")
        print(f"Branch: {run.branch}")
        print(f"Commit: {run.commit_sha[:8] if run.commit_sha else 'N/A'}")

        if run.duration_seconds:
            minutes = run.duration_seconds // 60
            seconds = run.duration_seconds % 60
            print(f"Duration: {run.duration_seconds}s ({minutes}m {seconds}s)")

        print(f"Started: {run.started_at}")
        if run.url:
            print(f"URL: {run.url}")

        # Display jobs
        print(f"\nJobs ({len(jobs)}):")
        if not jobs:
            print("  No jobs found. Fetch them with: scout ci fetch --workflow '{}' --with-jobs".format(
                run.workflow_name
            ))
        else:
            def format_job_line(job):
                """Format a single job line, avoiding duplication."""
                icon = "✓" if job.conclusion == "success" else "✗"
                duration = f"{job.duration_seconds}s" if job.duration_seconds else "N/A"

                # Check if job_name already contains platform/version info
                job_name = job.job_name
                has_platform_in_name = job.runner_os and job.runner_os in job_name
                has_version_in_name = job.python_version and job.python_version in job_name

                # Only add platform/version if not already in job name
                if (job.runner_os or job.python_version) and not (has_platform_in_name and has_version_in_name):
                    details = []
                    if job.runner_os and not has_platform_in_name:
                        details.append(job.runner_os)
                    if job.python_version and not has_version_in_name:
                        details.append(f"py{job.python_version}")
                    if details:
                        job_name = f"{job_name} [{', '.join(details)}]"

                return f"  {icon} {job_name} - {duration} (job_id: {job.job_id})"

            # Group and display based on --group-by option
            if args.group_by == "status":
                # Group by status
                passed = [j for j in jobs if j.conclusion == "success"]
                failed = [j for j in jobs if j.conclusion == "failure"]
                other = [j for j in jobs if j.conclusion not in ("success", "failure")]

                if failed:
                    print("\n  Failed:")
                    for job in failed:
                        print(f"  {format_job_line(job)}")

                if passed:
                    print(f"\n  Passed ({len(passed)}):")
                    for job in passed:
                        print(f"  {format_job_line(job)}")

                if other:
                    print(f"\n  Other ({len(other)}):")
                    for job in other:
                        print(f"  {format_job_line(job)}")

            elif args.group_by == "platform":
                # Group by runner OS
                by_platform = defaultdict(list)
                for job in jobs:
                    platform = job.runner_os or "unknown"
                    by_platform[platform].append(job)

                for platform in sorted(by_platform.keys()):
                    platform_jobs = by_platform[platform]
                    passed_count = sum(1 for j in platform_jobs if j.conclusion == "success")
                    print(f"\n  {platform} ({passed_count}/{len(platform_jobs)} passed):")
                    for job in platform_jobs:
                        print(f"  {format_job_line(job)}")

            else:  # none
                for job in jobs:
                    print(format_job_line(job))

            # Summary
            passed = [j for j in jobs if j.conclusion == "success"]
            failed = [j for j in jobs if j.conclusion == "failure"]
            other = [j for j in jobs if j.conclusion not in ("success", "failure")]

            print(f"\nSummary:")
            print(f"  Passed: {len(passed)}/{len(jobs)} ({len(passed)*100//len(jobs) if jobs else 0}%)")
            if failed:
                print(f"  Failed: {len(failed)}/{len(jobs)} ({len(failed)*100//len(jobs)}%)")
                print("\nView failed job details:")
                for job in failed:
                    print(f"  scout ci show --job-id {job.job_id}")
            if other:
                print(f"  Other: {len(other)}/{len(jobs)}")

        session.close()
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_ci_sync_command(args) -> int:
    """
    Handle 'ci sync' command to sync CI data to Anvil.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        from scout.integration.anvil_bridge import AnvilBridge

        # Create bridge
        bridge = AnvilBridge(args.db, args.anvil_db)

        if args.run_id:
            # Sync specific run
            if not args.quiet:
                print(f"Syncing run {args.run_id} to Anvil...")

            result = bridge.sync_ci_run_to_anvil(args.run_id, verbose=args.verbose)

            if not args.quiet:
                print(
                    f"\n✓ Synced run to Anvil validation run {result['validation_run_id']}"
                )
                print(f"  Tests synced: {result['tests_synced']}")
                print(f"  Jobs processed: {result['jobs_synced']}")

        else:
            # Sync recent runs
            if not args.quiet:
                workflow_msg = f" from workflow '{args.workflow}'" if args.workflow else ""
                print(f"Syncing {args.limit} recent runs{workflow_msg} to Anvil...")

            results = bridge.sync_recent_runs(
                limit=args.limit,
                workflow_name=args.workflow,
                verbose=args.verbose,
            )

            # Count successes
            successes = [r for r in results if "error" not in r]
            errors = [r for r in results if "error" in r]

            if not args.quiet:
                print(f"\n✓ Synced {len(successes)} run(s) to Anvil")
                if errors:
                    print(f"✗ Failed to sync {len(errors)} run(s)")
                    if args.verbose:
                        for error in errors:
                            print(f"  Run {error['run_id']}: {error['error']}")

                total_tests = sum(r.get("tests_synced", 0) for r in successes)
                print(f"\nTotal tests synced: {total_tests}")

        bridge.close()
        return 0

    except ImportError:
        print(
            "Error: Anvil not installed. Install with: pip install -e path/to/anvil",
            file=sys.stderr,
        )
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_ci_anvil_compare_command(args) -> int:
    """
    Handle 'ci anvil-compare' command to compare local vs CI results.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        from scout.integration.anvil_bridge import AnvilBridge

        # Create bridge
        bridge = AnvilBridge(args.db, args.anvil_db)

        if not args.quiet:
            print(f"Comparing local run {args.local_run} vs CI run {args.ci_run}...")

        comparison = bridge.compare_local_vs_ci(args.local_run, args.ci_run)

        # Display results
        print("\n=== Local vs CI Comparison ===\n")

        if comparison["pass_local_fail_ci"]:
            print(f"❌ Pass locally, FAIL in CI ({len(comparison['pass_local_fail_ci'])}):")
            for test in comparison["pass_local_fail_ci"]:
                print(f"  - {test}")
            print()

        if comparison["fail_local_pass_ci"]:
            print(f"⚠️  FAIL locally, pass in CI ({len(comparison['fail_local_pass_ci'])}):")
            for test in comparison["fail_local_pass_ci"]:
                print(f"  - {test}")
            print()

        if comparison["only_local"]:
            print(f"ℹ️  Only in local ({len(comparison['only_local'])}):")
            if args.verbose:
                for test in comparison["only_local"]:
                    print(f"  - {test}")
            else:
                print(f"  ({len(comparison['only_local'])} tests, use --verbose to see list)")
            print()

        if comparison["only_ci"]:
            print(f"ℹ️  Only in CI ({len(comparison['only_ci'])}):")
            if args.verbose:
                for test in comparison["only_ci"]:
                    print(f"  - {test}")
            else:
                print(f"  ({len(comparison['only_ci'])} tests, use --verbose to see list)")
            print()

        # Summary
        total_issues = len(comparison["pass_local_fail_ci"]) + len(
            comparison["fail_local_pass_ci"]
        )
        if total_issues == 0:
            print("✅ No significant differences found!")
        else:
            print(f"Total issues: {total_issues}")

        bridge.close()
        return 0

    except ImportError:
        print(
            "Error: Anvil not installed. Install with: pip install -e path/to/anvil",
            file=sys.stderr,
        )
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_ci_ci_failures_command(args) -> int:
    """
    Handle 'ci ci-failures' command to identify CI-specific failures.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        from scout.integration.anvil_bridge import AnvilBridge

        # Create bridge (anvil_db not strictly needed for this query)
        bridge = AnvilBridge(args.db, "dummy.db")

        if not args.quiet:
            print(
                f"Identifying tests that fail in CI (last {args.days} days, "
                f"min {args.min_failures} failures)..."
            )

        failures = bridge.identify_ci_specific_failures(
            days=args.days, min_failures=args.min_failures
        )

        if not failures:
            print("\n✅ No CI-specific failures found!")
            bridge.close()
            return 0

        # Display results
        print(f"\n=== CI-Specific Failures ({len(failures)} tests) ===\n")

        for i, failure in enumerate(failures, 1):
            platforms_str = ", ".join(failure["platforms"]) if failure["platforms"] else "unknown"
            last_fail_str = failure["last_failure"].strftime("%Y-%m-%d")

            print(f"{i}. {failure['test_name']}")
            print(f"   Failures: {failure['ci_failures']}")
            print(f"   Platforms: {platforms_str}")
            print(f"   Last failure: {last_fail_str}")
            print()

        # Suggestions
        print("💡 Suggestions:")
        print("  1. Check if these tests have platform-specific dependencies")
        print("  2. Run tests locally in Docker to reproduce CI environment")
        print("  3. Review test logs for environment-specific issues")
        print(f"\nView specific failure:")
        if failures:
            print(f"  scout ci patterns --type platform-specific")

        bridge.close()
        return 0

    except ImportError:
        print(
            "Error: Anvil not installed. Install with: pip install -e path/to/anvil",
            file=sys.stderr,
        )
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def handle_ci_command(args) -> int:
    """
    Route to appropriate CI subcommand handler.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    if args.ci_command == "fetch":
        return handle_ci_fetch_command(args)
    elif args.ci_command == "download":
        return handle_ci_download_command(args)
    elif args.ci_command == "analyze":
        return handle_ci_analyze_command(args)
    elif args.ci_command == "compare":
        return handle_ci_compare_command(args)
    elif args.ci_command == "patterns":
        return handle_ci_patterns_command(args)
    elif args.ci_command == "show":
        return handle_ci_show_command(args)
    elif args.ci_command == "sync":
        return handle_ci_sync_command(args)
    elif args.ci_command == "anvil-compare":
        return handle_ci_anvil_compare_command(args)
    elif args.ci_command == "ci-failures":
        return handle_ci_ci_failures_command(args)
    else:
        print(f"Unknown CI subcommand: {args.ci_command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
