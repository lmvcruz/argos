"""
Main CLI entry point for Anvil.

This module provides the command-line interface for Anvil using argparse.
"""

import argparse
import sys

from anvil.cli.commands import (
    check_command,
    config_check_tools_command,
    config_init_command,
    config_show_command,
    config_validate_command,
    execute_command,
    history_show_command,
    install_hooks_command,
    list_command,
    rules_list_command,
    stats_export_command,
    stats_flaky_command,
    stats_flaky_tests_command,
    stats_problem_files_command,
    stats_report_command,
    stats_show_command,
    stats_trends_command,
)
from anvil.utils.encoding import configure_unicode_output

# Version
__version__ = "0.1.0"


def create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for Anvil CLI.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="anvil",
        description="Anvil - Code Quality Gate Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--version", action="version", version=f"Anvil {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'check' command
    check_parser = subparsers.add_parser("check", help="Run code quality validation")
    check_parser.add_argument(
        "--incremental",
        action="store_true",
        help="Run on changed files only (git)",
    )
    check_parser.add_argument(
        "--language",
        choices=["python", "cpp"],
        help="Filter by specific language",
    )
    check_parser.add_argument(
        "--validator",
        help="Run specific validator only",
    )
    check_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output",
    )
    check_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Show only errors",
    )
    check_parser.add_argument(
        "--format",
        choices=["console", "json"],
        default="console",
        help="Output format",
    )
    check_parser.add_argument(
        "--parsed",
        action="store_true",
        help="Show parsed data in Verdict-compatible format",
    )
    check_parser.add_argument(
        "files",
        nargs="*",
        help="Specific files to check",
    )

    # 'parse' command - Parse tool output without running tools
    parse_parser = subparsers.add_parser("parse", help="Parse tool output and display parsed data")
    parse_parser.add_argument(
        "--tool",
        required=True,
        choices=["black", "flake8", "isort", "pylint", "pytest", "coverage"],
        help="Tool that produced the output",
    )
    parse_parser.add_argument(
        "--input",
        "-i",
        type=str,
        help="Tool output as string (use - for stdin)",
    )
    parse_parser.add_argument(
        "--file",
        "-f",
        type=str,
        help="Read tool output from file",
    )

    # 'install-hooks' command
    hooks_parser = subparsers.add_parser("install-hooks", help="Install or uninstall git hooks")
    hooks_parser.add_argument(
        "--pre-push",
        action="store_true",
        help="Install pre-push hook instead of pre-commit",
    )
    hooks_parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall git hooks",
    )
    hooks_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )

    # 'config' subcommands
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(
        dest="config_command", help="Configuration commands"
    )

    # 'config show'
    config_show_parser = config_subparsers.add_parser("show", help="Display current configuration")
    config_show_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )

    # 'config validate'
    config_validate_parser = config_subparsers.add_parser(
        "validate", help="Validate anvil.toml file"
    )
    config_validate_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )

    # 'config init'
    config_init_parser = config_subparsers.add_parser("init", help="Generate default anvil.toml")
    config_init_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )

    # 'config check-tools'
    config_tools_parser = config_subparsers.add_parser(
        "check-tools", help="Check availability of validators"
    )
    config_tools_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )

    # 'list' command
    list_parser = subparsers.add_parser("list", help="List available validators")
    list_parser.add_argument(
        "--language",
        choices=["python", "cpp"],
        help="Filter by specific language",
    )
    list_parser.add_argument(
        "--detailed",
        "-d",
        action="store_true",
        help="Show detailed information",
    )
    list_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )

    # 'stats' subcommands
    stats_parser = subparsers.add_parser("stats", help="Statistics and reporting")
    stats_subparsers = stats_parser.add_subparsers(dest="stats_command", help="Statistics commands")

    # 'stats report'
    stats_report_parser = stats_subparsers.add_parser("report", help="Show statistics summary")
    stats_report_parser.add_argument(
        "--days",
        type=int,
        help="Filter by last N days",
    )
    stats_report_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )
    stats_report_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output",
    )

    # 'stats export'
    stats_export_parser = stats_subparsers.add_parser("export", help="Export statistics data")
    stats_export_parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Export format",
    )
    stats_export_parser.add_argument(
        "--output",
        "-o",
        help="Output file path",
    )
    stats_export_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )

    # 'stats flaky'
    stats_flaky_parser = stats_subparsers.add_parser("flaky", help="List flaky tests")
    stats_flaky_parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Success rate threshold (0.0-1.0)",
    )
    stats_flaky_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )

    # 'stats problem-files'
    stats_problem_parser = stats_subparsers.add_parser(
        "problem-files", help="List files with frequent issues"
    )
    stats_problem_parser.add_argument(
        "--threshold",
        type=int,
        default=3,
        help="Minimum error count threshold",
    )
    stats_problem_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )

    # 'stats trends'
    stats_trends_parser = stats_subparsers.add_parser("trends", help="Show validation trends")
    stats_trends_parser.add_argument(
        "--validator",
        help="Filter by specific validator",
    )
    stats_trends_parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to analyze",
    )
    stats_trends_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )
    stats_trends_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output",
    )

    # 'stats show' - new command for execution statistics
    stats_show_parser = stats_subparsers.add_parser("show", help="Show entity statistics")
    stats_show_parser.add_argument(
        "--type",
        dest="entity_type",
        default="test",
        help="Entity type (test, coverage, lint)",
    )
    stats_show_parser.add_argument(
        "--window",
        type=int,
        default=20,
        help="Number of recent executions to analyze",
    )
    stats_show_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )

    # 'stats flaky-tests' - enhanced flaky detection using execution history
    stats_flaky_tests_parser = stats_subparsers.add_parser(
        "flaky-tests", help="Show flaky tests based on execution history"
    )
    stats_flaky_tests_parser.add_argument(
        "--threshold",
        type=float,
        default=0.10,
        help="Failure rate threshold (0.0-1.0, default 0.10 = 10%%)",
    )
    stats_flaky_tests_parser.add_argument(
        "--window",
        type=int,
        default=20,
        help="Number of recent executions to analyze",
    )
    stats_flaky_tests_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )

    # 'execute' command - selective test execution with rules
    execute_parser = subparsers.add_parser("execute", help="Execute tests using a rule")
    execute_parser.add_argument(
        "--rule",
        required=True,
        help="Name of the rule to execute",
    )
    execute_parser.add_argument(
        "--config",
        dest="config_path",
        help="Path to anvil.toml configuration file",
    )
    execute_parser.add_argument(
        "--execution-id",
        help="Optional execution ID (auto-generated if not provided)",
    )
    execute_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output",
    )
    execute_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )

    # 'rules' command - manage execution rules
    rules_parser = subparsers.add_parser("rules", help="Manage execution rules")
    rules_subparsers = rules_parser.add_subparsers(dest="rules_command", help="Rules commands")

    # 'rules list'
    rules_list_parser = rules_subparsers.add_parser("list", help="List execution rules")
    rules_list_parser.add_argument(
        "--enabled-only",
        action="store_true",
        help="Show only enabled rules",
    )
    rules_list_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )

    # 'history' command - view execution history
    history_parser = subparsers.add_parser("history", help="View execution history")
    history_subparsers = history_parser.add_subparsers(
        dest="history_command", help="History commands"
    )

    # 'history show'
    history_show_parser = history_subparsers.add_parser(
        "show", help="Show execution history for an entity"
    )
    history_show_parser.add_argument(
        "--entity",
        required=True,
        help="Entity ID (e.g., test nodeid)",
    )
    history_show_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of recent executions to show",
    )
    history_show_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )

    return parser


def main(argv=None) -> int:
    """
    Main entry point for Anvil CLI.

    Args:
        argv: Command line arguments (for testing)

    Returns:
        Exit code
    """
    # Configure Unicode output for Windows compatibility
    configure_unicode_output()

    parser = create_parser()
    args = parser.parse_args(argv)

    # If no command specified, show help
    if not args.command:
        parser.print_help()
        return 0

    # Dispatch to command handlers
    try:
        if args.command == "check":
            return check_command(
                args,
                incremental=args.incremental,
                language=args.language,
                validator=args.validator,
                verbose=args.verbose,
                quiet=args.quiet,
                format=args.format,
                parsed=args.parsed,
                files=args.files if args.files else None,
            )

        elif args.command == "parse":
            from anvil.cli.commands import parse_command

            return parse_command(
                args,
                tool=args.tool,
                input_text=args.input,
                input_file=args.file,
            )

        elif args.command == "install-hooks":
            return install_hooks_command(
                args,
                pre_push=args.pre_push,
                uninstall=args.uninstall,
                quiet=args.quiet,
            )

        elif args.command == "config":
            if args.config_command == "show":
                return config_show_command(args, quiet=args.quiet)
            elif args.config_command == "validate":
                return config_validate_command(args, quiet=args.quiet)
            elif args.config_command == "init":
                return config_init_command(args, quiet=args.quiet)
            elif args.config_command == "check-tools":
                return config_check_tools_command(args, quiet=args.quiet)
            else:
                parser.parse_args(["config", "--help"])
                return 0

        elif args.command == "list":
            return list_command(
                args,
                language=args.language,
                detailed=args.detailed,
                quiet=args.quiet,
            )

        elif args.command == "stats":
            if args.stats_command == "report":
                return stats_report_command(
                    args,
                    days=args.days,
                    quiet=args.quiet,
                    verbose=args.verbose,
                )
            elif args.stats_command == "export":
                return stats_export_command(
                    args,
                    format=args.format,
                    output=args.output,
                    quiet=args.quiet,
                )
            elif args.stats_command == "flaky":
                return stats_flaky_command(
                    args,
                    threshold=args.threshold,
                    quiet=args.quiet,
                )
            elif args.stats_command == "problem-files":
                return stats_problem_files_command(
                    args,
                    threshold=args.threshold,
                    quiet=args.quiet,
                )
            elif args.stats_command == "trends":
                return stats_trends_command(
                    args,
                    validator=args.validator,
                    days=args.days,
                    quiet=args.quiet,
                    verbose=args.verbose,
                )
            elif args.stats_command == "show":
                return stats_show_command(
                    args,
                    entity_type=args.entity_type,
                    window=args.window,
                    quiet=args.quiet,
                )
            elif args.stats_command == "flaky-tests":
                return stats_flaky_tests_command(
                    args,
                    threshold=args.threshold,
                    window=args.window,
                    quiet=args.quiet,
                )
            else:
                parser.parse_args(["stats", "--help"])
                return 0

        elif args.command == "execute":
            return execute_command(
                args,
                rule=args.rule,
                config_path=args.config_path,
                execution_id=args.execution_id,
                verbose=args.verbose,
                quiet=args.quiet,
            )

        elif args.command == "rules":
            if args.rules_command == "list":
                return rules_list_command(
                    args,
                    enabled_only=args.enabled_only,
                    quiet=args.quiet,
                )
            else:
                parser.parse_args(["rules", "--help"])
                return 0

        elif args.command == "history":
            if args.history_command == "show":
                return history_show_command(
                    args,
                    entity=args.entity,
                    limit=args.limit,
                    quiet=args.quiet,
                )
            else:
                parser.parse_args(["history", "--help"])
                return 0

        else:
            parser.print_help()
            return 0

    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
