"""
Scout CLI argument parser with four-stage pipeline support.

Provides the new CLI structure for fetch, parse, and sync commands
with flexible case identification and skip options.
"""

import argparse
from typing import Optional


def create_new_parser() -> argparse.ArgumentParser:
    """
    Create and configure the new Scout argument parser.

    Supports:
    - scout fetch <triple> [--output file] [--save]
    - scout fetch --fetch-all [--output dir] [--save]
    - scout fetch --fetch-last N [--workflow-name X] [--output dir] [--save]
    - scout parse --input file [--output out] [--save]
    - scout parse <triple> [--output out] [--save]
    - scout sync <triple> [--skip-*]
    - scout sync --fetch-all [--skip-*]
    - scout sync --fetch-last N [--workflow-name X] [--skip-*]

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="scout",
        description="Scout - CI/CD inspection and analysis tool with four-stage pipeline",
        epilog="For more information, visit https://github.com/lmvcruz/argos",
    )

    parser.add_argument("--version", action="version", version="Scout 1.0.0")

    # Create parent parser for common options
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "--token",
        help="GitHub personal access token (or use GITHUB_TOKEN env var)",
    )
    common_parser.add_argument(
        "--repo",
        help="GitHub repository in owner/repo format (or use GITHUB_REPO env var)",
    )
    common_parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    common_parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress non-error output"
    )
    common_parser.add_argument(
        "--db",
        default="scout.db",
        help="Path to Scout database (default: scout.db)",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # ==================== FETCH COMMAND ====================
    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Fetch CI logs from GitHub",
        parents=[common_parser],
        description="Download CI logs from GitHub Actions with multiple output options",
    )

    # Fetch mode options (user must provide one of these patterns)
    fetch_parser.add_argument(
        "--fetch-all",
        action="store_true",
        help="Fetch all available executions from workflow",
    )
    fetch_parser.add_argument(
        "--fetch-last",
        type=int,
        metavar="N",
        help="Fetch last N executions",
    )
    fetch_parser.add_argument(
        "--workflow-name",
        help="Workflow name (required for single execution fetch)",
    )

    # Case identifier (only for single fetch mode)
    fetch_parser.add_argument(
        "--run-id",
        type=int,
        help="GitHub Actions run ID",
    )
    fetch_parser.add_argument(
        "--execution-number",
        type=int,
        help="Execution number (sequential within workflow)",
    )
    fetch_parser.add_argument(
        "--job-id",
        help="GitHub Actions job ID",
    )
    fetch_parser.add_argument(
        "--action-name",
        help="User-friendly action/job name",
    )

    # Output options
    fetch_parser.add_argument(
        "--output",
        help="Output file path (saves logs to file instead of stdout)",
    )
    fetch_parser.add_argument(
        "--save",
        action="store_true",
        help="Save logs to execution database",
    )

    fetch_parser.set_defaults(func="fetch")

    # ==================== PARSE COMMAND ====================
    parse_parser = subparsers.add_parser(
        "parse",
        help="Parse CI logs using Anvil parsers",
        parents=[common_parser],
        description="Parse raw CI logs or retrieve from database and parse",
    )

    # Parse source options (user must provide one)
    parse_parser.add_argument(
        "--input",
        help="Input file path (parse raw logs from file)",
    )
    parse_parser.add_argument(
        "--workflow-name",
        help="Workflow name (parse from database)",
    )

    # Case identifier (only when using --workflow-name)
    parse_parser.add_argument(
        "--run-id",
        type=int,
        help="GitHub Actions run ID",
    )
    parse_parser.add_argument(
        "--execution-number",
        type=int,
        help="Execution number (sequential within workflow)",
    )
    parse_parser.add_argument(
        "--job-id",
        help="GitHub Actions job ID",
    )
    parse_parser.add_argument(
        "--action-name",
        help="User-friendly action/job name",
    )

    # Output options
    parse_parser.add_argument(
        "--output",
        help="Output file path (saves parsed results to file)",
    )
    parse_parser.add_argument(
        "--save",
        action="store_true",
        help="Save parsed results to analysis database",
    )

    parse_parser.set_defaults(func="parse")

    # ==================== SYNC COMMAND ====================
    sync_parser = subparsers.add_parser(
        "sync",
        help="Run four-stage pipeline: fetch → save-ci → parse → save-analysis",
        parents=[common_parser],
        description="Sync CI data through all pipeline stages with skip options",
    )

    # Sync mode options (user must provide one of these patterns)
    sync_parser.add_argument(
        "--fetch-all",
        action="store_true",
        help="Sync all available executions from workflow",
    )
    sync_parser.add_argument(
        "--fetch-last",
        type=int,
        metavar="N",
        help="Sync last N executions",
    )
    sync_parser.add_argument(
        "--workflow-name",
        help="Workflow name (required for single execution sync)",
    )

    # Case identifier (only for single sync mode)
    sync_parser.add_argument(
        "--run-id",
        type=int,
        help="GitHub Actions run ID",
    )
    sync_parser.add_argument(
        "--execution-number",
        type=int,
        help="Execution number (sequential within workflow)",
    )
    sync_parser.add_argument(
        "--job-id",
        help="GitHub Actions job ID",
    )
    sync_parser.add_argument(
        "--action-name",
        help="User-friendly action/job name",
    )

    # Skip options
    sync_parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip fetch stage (use cached execution data)",
    )
    sync_parser.add_argument(
        "--skip-save-ci",
        action="store_true",
        help="Skip save-ci stage (don't persist raw logs)",
    )
    sync_parser.add_argument(
        "--skip-parse",
        action="store_true",
        help="Skip parse stage (don't parse logs)",
    )
    sync_parser.add_argument(
        "--skip-save-analysis",
        action="store_true",
        help="Skip save-analysis stage (don't persist parsed results)",
    )

    sync_parser.set_defaults(func="sync")

    return parser


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        args: Optional list of arguments (for testing)

    Returns:
        Parsed arguments namespace
    """
    parser = create_new_parser()
    return parser.parse_args(args)
