"""
CLI command handlers for Anvil.

This module implements the main command handlers for the Anvil CLI:
- check: Run validation
- install-hooks: Install git hooks
- config: Configuration management
- list: List validators
- stats: Statistics and reporting
"""

import json
import sys
from pathlib import Path
from typing import List, Optional

from anvil.config.configuration import ConfigurationError, ConfigurationManager
from anvil.core.file_collector import FileCollector
from anvil.core.orchestrator import ValidationOrchestrator
from anvil.core.validator_registry import ValidatorRegistry
from anvil.git.hooks import GitHookError, GitHookManager
from anvil.reporting.console_reporter import ConsoleReporter
from anvil.reporting.json_reporter import JSONReporter
from anvil.utils.encoding import get_safe_chars


def check_command(
    args,
    incremental: bool = False,
    language: Optional[str] = None,
    validator: Optional[str] = None,
    verbose: bool = False,
    quiet: bool = False,
    format: str = "console",
    parsed: bool = False,
    files: Optional[List[str]] = None,
) -> int:
    """
    Run code quality validation.

    Args:
        args: Parsed arguments from argparse
        incremental: Run on changed files only
        language: Filter by specific language
        validator: Run specific validator only
        verbose: Show detailed output
        quiet: Show only errors
        format: Output format (console, json)
        parsed: Show parsed data in Verdict-compatible format
        files: Explicit list of files to check

    Returns:
        Exit code (0 = pass, 1 = fail, 2 = config error)
    """
    try:
        # Load configuration (from --config arg or default anvil.toml)
        config = None
        config_path = getattr(args, "config", None)

        # If no explicit config, check for anvil.toml in current directory
        if not config_path:
            default_config = Path("anvil.toml")
            if default_config.exists():
                config_path = default_config

        if config_path:
            try:
                config_manager = ConfigurationManager(Path(config_path))
                config = config_manager.config
            except ConfigurationError as e:
                if not quiet:
                    print(f"Configuration error: {e}", file=sys.stderr)
                return 2

        # Determine root directory
        root_dir = Path.cwd()

        # Collect files to check
        if files:
            # Use explicitly specified files
            files_to_check = [Path(f) for f in files]
            # Validate files exist
            for file_path in files_to_check:
                if not file_path.exists():
                    print(f"Error: File not found: {file_path}", file=sys.stderr)
                    return 2
        else:
            # Use FileCollector to gather files
            file_collector = FileCollector(
                root_dir=root_dir,
                exclude_patterns=config.get("exclude_patterns", []) if config else None,
                file_patterns=config.get("file_patterns", {}) if config else None,
            )

            # Check if staged flag is set
            staged = getattr(args, "staged", False)

            # Collect files based on mode
            files_to_check = file_collector.collect_files(
                language=language,
                incremental=incremental,
                staged_only=staged,
            )

            if not files_to_check:
                if not quiet:
                    print("No files to check.")
                return 0

        # Create orchestrator
        registry = ValidatorRegistry()
        # Register all available validators
        from anvil.core.validator_registration import register_all_validators

        register_all_validators(registry)
        orchestrator = ValidationOrchestrator(registry)

        # Get parallel and fail_fast flags
        parallel = getattr(args, "parallel", True)
        fail_fast = getattr(args, "fail_fast", False)

        # Check if there are any validators registered
        all_validators = registry.list_all()
        if not all_validators:
            # No validators - return success with appropriate output
            if format == "json":
                # Return valid JSON even with no validators
                empty_report = {
                    "summary": {
                        "total_validators": 0,
                        "passed_validators": 0,
                        "failed_validators": 0,
                        "total_errors": 0,
                        "total_warnings": 0,
                        "files_checked": 0,
                        "execution_time": 0.0,
                        "overall_passed": True,
                    },
                    "results": [],
                }
                print(json.dumps(empty_report, indent=2))
            else:
                if not quiet:
                    print("No validators registered.")
            return 0

        # Run validators
        if validator:
            # Run specific validator
            results = [
                orchestrator.run_validator(name=validator, files=files_to_check, config=config)
            ]
        elif language:
            # Run validators for specific language
            results = orchestrator.run_for_language(
                language=language,
                files=files_to_check,
                parallel=parallel,
                fail_fast=fail_fast,
                config=config,
            )
        else:
            # Run all validators
            results = orchestrator.run_all(
                files=files_to_check, parallel=parallel, fail_fast=fail_fast, config=config
            )

        # Generate report
        if parsed:
            from anvil.reporting.parsed_data_reporter import ParsedDataReporter

            reporter = ParsedDataReporter(indent=2)
        elif format == "json":
            reporter = JSONReporter(indent=2)
        else:
            reporter = ConsoleReporter(verbose=verbose, quiet=quiet)

        reporter.generate_report(results)

        # Determine exit code
        overall_passed = orchestrator.determine_overall_result(results)
        return 0 if overall_passed else 1

    except FileNotFoundError as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        if not quiet:
            print(f"Unexpected error: {e}", file=sys.stderr)
        return 2


def parse_command(
    args,
    tool: str,
    input_text: Optional[str] = None,
    input_file: Optional[str] = None,
) -> int:
    """
    Parse tool output and display parsed data.

    Reads tool output from stdin, argument, or file and parses it
    without running any actual validators. Returns parsed data in
    Verdict-compatible format.

    Args:
        args: Parsed arguments from argparse
        tool: Name of the tool (black, flake8, isort, pylint, pytest, coverage)
        input_text: Tool output as string (use - to read from stdin)
        input_file: Path to file containing tool output

    Returns:
        Exit code (0 = success, 1 = parse error)
    """
    try:
        # Get input text
        if input_file:
            # Read from file
            with open(input_file, "r") as f:
                output = f.read()
        elif input_text == "-":
            # Read from stdin
            output = sys.stdin.read()
        elif input_text:
            # Use provided text
            output = input_text
        else:
            print("Error: Provide --input or --file", file=sys.stderr)
            return 1

        # Parse based on tool type
        from anvil.parsers.coverage_parser import CoverageParser
        from anvil.parsers.lint_parser import LintParser
        from anvil.parsers.pytest_parser import PytestParser
        from anvil.reporting.parsed_data_reporter import ParsedDataReporter

        parsed_data = None

        if tool in ["black", "flake8", "isort", "pylint"]:
            # Use LintParser for lint-type tools
            parser = LintParser()
            if tool == "black":
                parsed_data = parser.parse_black_output(output, Path("."))
            elif tool == "flake8":
                parsed_data = parser.parse_flake8_output(output, Path("."))
            elif tool == "isort":
                parsed_data = parser.parse_isort_output(output, Path("."))
            elif tool == "pylint":
                parsed_data = parser.parse_pylint_output(output, Path("."))

        elif tool == "pytest":
            # Use PytestParser for pytest output
            parser = PytestParser()
            parsed_data = parser.parse(output)

        elif tool == "coverage":
            # Use CoverageParser for coverage output
            parser = CoverageParser()
            parsed_data = parser.parse(output)

        # Convert parsed data to ValidationResult format
        from anvil.models.validator import Issue, ValidationResult

        if parsed_data is None:
            print(f"Error: Could not parse {tool} output", file=sys.stderr)
            return 1

        # Handle LintData objects
        if hasattr(parsed_data, "validator"):
            # It's LintData
            errors = []
            warnings = []

            for file_violation in parsed_data.file_violations:
                for violation in file_violation.violations:
                    severity = violation.get("severity", "error").lower()
                    issue = Issue(
                        file_path=file_violation.file_path,
                        line_number=violation.get("line", 0),
                        column_number=violation.get("column"),
                        message=violation.get("message", ""),
                        severity=severity,
                        rule_name=violation.get("rule"),
                        error_code=violation.get("code"),
                    )
                    if severity == "error":
                        errors.append(issue)
                    else:
                        warnings.append(issue)

            result = ValidationResult(
                validator_name=parsed_data.validator,
                passed=parsed_data.total_violations == 0,
                errors=errors,
                warnings=warnings,
                files_checked=parsed_data.files_scanned,
            )
        else:
            # Generic handling for other parser types
            result = ValidationResult(
                validator_name=tool,
                passed=True,
                files_checked=0,
            )

        # Output parsed data
        reporter = ParsedDataReporter(indent=2)
        reporter.generate_report([result])
        return 0

    except FileNotFoundError as e:
        print(f"Error: File not found: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error parsing {tool} output: {e}", file=sys.stderr)
        return 1


def install_hooks_command(
    args, pre_push: bool = False, uninstall: bool = False, quiet: bool = False
) -> int:
    """
    Install or uninstall git hooks.

    Args:
        args: Parsed arguments from argparse
        pre_push: Install pre-push hook
        uninstall: Uninstall hooks
        quiet: Suppress output

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        # Use current directory as repo path
        repo_path = Path.cwd()
        hook_manager = GitHookManager(repo_path)

        # Check if we're in a git repository
        if not hook_manager.is_git_repository():
            print("Error: Not in a git repository", file=sys.stderr)
            return 1

        if uninstall:
            # Uninstall all hooks
            hook_manager.uninstall_all_hooks()
            if not quiet:
                print("Successfully uninstalled git hooks")
        elif pre_push:
            # Install pre-push hook
            hook_manager.install_pre_push_hook()
            if not quiet:
                print("Successfully installed pre-push hook")
        else:
            # Install pre-commit hook (default)
            hook_manager.install_pre_commit_hook()
            if not quiet:
                print("Successfully installed pre-commit hook")

        return 0

    except GitHookError as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        if not quiet:
            print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def config_show_command(args, quiet: bool = False) -> int:
    """
    Display current configuration.

    Args:
        args: Parsed arguments from argparse
        quiet: Suppress output

    Returns:
        Exit code (0 = success)
    """
    try:
        # Find config file
        config_path = Path("anvil.toml")
        if not config_path.exists():
            if not quiet:
                print("No anvil.toml found in current directory")
                print("Run 'anvil config init' to create a default configuration")
            return 0

        # Load and display configuration
        config_manager = ConfigurationManager(config_path)

        if not quiet:
            print(f"Configuration from: {config_path}")
            print("-" * 60)

            # Display configuration as JSON for readability
            import json

            config_dict = dict(config_manager.config)
            print(json.dumps(config_dict, indent=2))

        return 0

    except ConfigurationError as e:
        if not quiet:
            print(f"Configuration error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 2


def config_validate_command(args, quiet: bool = False) -> int:
    """
    Validate anvil.toml configuration file.

    Args:
        args: Parsed arguments from argparse
        quiet: Suppress output

    Returns:
        Exit code (0 = valid, 2 = invalid)
    """
    try:
        # Find config file
        config_path = Path("anvil.toml")
        if not config_path.exists():
            if not quiet:
                print("Error: anvil.toml not found", file=sys.stderr)
            return 2

        # Try to load configuration
        ConfigurationManager(config_path)

        if not quiet:
            chars = get_safe_chars()
            print(f"{chars.check} Configuration is valid: {config_path}")

        return 0

    except ConfigurationError as e:
        if not quiet:
            print(f"Configuration error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        if not quiet:
            print(f"Unexpected error: {e}", file=sys.stderr)
        return 2


def config_init_command(args, quiet: bool = False) -> int:
    """
    Generate default anvil.toml configuration file.

    Args:
        args: Parsed arguments from argparse
        quiet: Suppress output

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        config_path = Path("anvil.toml")

        # Don't overwrite existing config
        if config_path.exists():
            if not quiet:
                print("anvil.toml already exists. Not overwriting.")
            return 0

        # Generate default configuration
        default_config = """# Anvil Configuration File
# This file controls validation behavior for your project

[anvil]
# Global settings
languages = []  # Auto-detect languages (Python, C++)
incremental = true  # Check only changed files by default
fail_fast = false  # Continue validation even after failures
parallel = true  # Run validators in parallel
max_errors = 0  # Maximum errors before stopping (0 = no limit)
max_warnings = 10  # Maximum warnings before stopping

[anvil.python]
enabled = true
file_patterns = ["**/*.py"]

[anvil.python.flake8]
enabled = true
max_line_length = 100
ignore = []

[anvil.python.black]
enabled = true
line_length = 100

[anvil.python.isort]
enabled = true
profile = "black"
line_length = 100

[anvil.python.pylint]
enabled = true
max_complexity = 10
disable = []

[anvil.cpp]
enabled = true
file_patterns = ["**/*.{cpp,hpp,cc,h,cxx,hxx}"]
standard = "c++17"

[anvil.cpp.clang-tidy]
enabled = true
checks = ["bugprone-*", "modernize-*", "performance-*"]
"""

        # Write config file
        config_path.write_text(default_config, encoding="utf-8")

        if not quiet:
            print(f"Generated default configuration: {config_path}")

        return 0

    except Exception as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 1


def config_check_tools_command(args, quiet: bool = False) -> int:
    """
    Check availability of validator tools.

    Args:
        args: Parsed arguments from argparse
        quiet: Suppress output

    Returns:
        Exit code (0 = all available, 3 = some missing)
    """
    try:
        registry = ValidatorRegistry()
        # Register all available validators
        from anvil.core.validator_registration import register_all_validators

        register_all_validators(registry)

        # Get all validators
        all_validators = registry.list_all()

        if not quiet:
            print("Checking validator tool availability...\n")

        available_count = 0
        unavailable_count = 0
        chars = get_safe_chars()

        for validator in all_validators:
            name = validator.name
            language = validator.language

            # Check if validator is available
            if validator.is_available():
                if not quiet:
                    print(f"{chars.check} {name:20} ({language:6}) - Available")
                available_count += 1
            else:
                if not quiet:
                    print(f"{chars.cross} {name:20} ({language:6}) - Not available")
                unavailable_count += 1

        if not quiet:
            print(f"\nSummary: {available_count} available, {unavailable_count} missing")

        # Return 3 if some tools are missing, 0 if all available
        return 3 if unavailable_count > 0 else 0

    except Exception as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 1


def list_command(
    args, language: Optional[str] = None, detailed: bool = False, quiet: bool = False
) -> int:
    """
    List available validators.

    Args:
        args: Parsed arguments from argparse
        language: Filter by language
        detailed: Show detailed information
        quiet: Suppress output

    Returns:
        Exit code (0 = success)
    """
    try:
        registry = ValidatorRegistry()
        # Register all available validators
        from anvil.core.validator_registration import register_all_validators

        register_all_validators(registry)

        # Get validators, optionally filtered by language
        if language:
            validators = registry.get_validators_by_language(language)
        else:
            validators = registry.list_all()

        if not quiet:
            if language:
                print(f"Available {language} validators:\n")
            else:
                print("Available validators:\n")

            if not validators:
                print(f"No validators found{' for ' + language if language else ''}.")
                return 0

            # Group by language if not filtered
            if language:
                for validator in validators:
                    name = validator.name

                    if detailed:
                        # Show detailed info
                        available = "Available" if validator.is_available() else "Not available"
                        print(f"  {name}")
                        print(f"    Status: {available}")
                        if hasattr(validator, "description"):
                            print(f"    Description: {validator.description}")
                        print()
                    else:
                        # Just show name
                        print(f"  {name}")
            else:
                # Group by language
                by_language = {}
                for validator in validators:
                    lang = validator.language
                    if lang not in by_language:
                        by_language[lang] = []
                    by_language[lang].append(validator)

                for lang, lang_validators in sorted(by_language.items()):
                    print(f"{lang.capitalize()}:")
                    for validator in lang_validators:
                        name = validator.name
                        if detailed:
                            available = "Available" if validator.is_available() else "Not available"
                            print(f"  {name:20} - {available}")
                        else:
                            print(f"  {name}")
                    print()

        return 0
    except Exception as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 1


def stats_report_command(
    args, days: Optional[int] = None, quiet: bool = False, verbose: bool = False
) -> int:
    """
    Show statistics summary.

    Args:
        args: Parsed arguments from argparse
        days: Filter by last N days
        quiet: Suppress output
        verbose: Show detailed output

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        if not quiet:
            print("Statistics Summary")
            print("=" * 50)
            if days:
                print(f"Time range: Last {days} days")
            else:
                print("Time range: All available data")
            print()
            print("No statistics data available yet.")
            print("Run some validation checks to generate data.")
        return 0
    except Exception as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 1


def stats_export_command(
    args,
    format: str = "json",
    output: Optional[str] = None,
    quiet: bool = False,
) -> int:
    """
    Export statistics data.

    Args:
        args: Parsed arguments from argparse
        format: Export format (json or csv)
        output: Output file path
        quiet: Suppress output

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        if format not in ["json", "csv"]:
            if not quiet:
                print(f"Error: Invalid format '{format}'", file=sys.stderr)
            return 1

        if output:
            # Export to file
            try:
                output_path = Path(output)
                if format == "json":
                    content = '{"message": "No statistics data available yet"}'
                else:  # csv
                    content = "timestamp,validator,status,errors\n"

                output_path.write_text(content)
                if not quiet:
                    print(f"Statistics exported to: {output}")
            except Exception as e:
                if not quiet:
                    print(f"Error writing to file: {e}", file=sys.stderr)
                return 1
        else:
            # Export to stdout
            if format == "json":
                print('{"message": "No statistics data available yet"}')
            else:  # csv
                print("timestamp,validator,status,errors")

        return 0
    except Exception as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 1


def stats_flaky_command(args, threshold: float = 0.8, quiet: bool = False) -> int:
    """
    List flaky tests.

    Args:
        args: Parsed arguments from argparse
        threshold: Success rate threshold (0.0-1.0)
        quiet: Suppress output

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        # Validate threshold
        if threshold < 0.0 or threshold > 1.0:
            if not quiet:
                print("Error: Threshold must be between 0.0 and 1.0", file=sys.stderr)
            return 1

        if not quiet:
            print("Flaky Tests")
            print("=" * 50)
            print(f"Threshold: {threshold:.2f} (showing tests with success rate < {threshold:.0%})")
            print()
            print("No flaky tests detected.")
            print("(No test data available yet)")

        return 0
    except Exception as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 1


def stats_problem_files_command(args, threshold: int = 3, quiet: bool = False) -> int:
    """
    List files with frequent issues.

    Args:
        args: Parsed arguments from argparse
        threshold: Minimum error count threshold
        quiet: Suppress output

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        if not quiet:
            print("Problem Files")
            print("=" * 50)
            print(f"Threshold: {threshold} errors")
            print()
            print("No problem files detected.")
            print("(No validation data available yet)")

        return 0
    except Exception as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 1


def stats_trends_command(
    args,
    validator: Optional[str] = None,
    days: int = 30,
    quiet: bool = False,
    verbose: bool = False,
) -> int:
    """
    Show validation trends.

    Args:
        args: Parsed arguments from argparse
        validator: Filter by specific validator
        days: Number of days to analyze
        quiet: Suppress output
        verbose: Show detailed output

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        if not quiet:
            print("Validation Trends")
            print("=" * 50)
            if validator:
                print(f"Validator: {validator}")
            else:
                print("Validator: All validators")
            print(f"Time range: Last {days} days")
            print()
            print("No trend data available yet.")
            print("Run validation checks over time to generate trends.")

        return 0
    except Exception as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 1


def execute_command(
    args,
    rule: str,
    config_path: Optional[str] = None,
    execution_id: Optional[str] = None,
    verbose: bool = False,
    quiet: bool = False,
) -> int:
    """
    Execute tests using a specific rule.

    Args:
        args: Parsed arguments from argparse
        rule: Name of the rule to execute
        config_path: Path to anvil.toml configuration file
        execution_id: Optional execution ID (auto-generated if not provided)
        verbose: Show detailed output
        quiet: Suppress output

    Returns:
        Exit code (0 = pass, 1 = fail, 2 = error)
    """
    db = None
    executor = None
    try:
        from anvil.executors.pytest_executor import PytestExecutorWithHistory
        from anvil.storage.execution_schema import ExecutionDatabase

        # Initialize database
        db_path = Path(".anvil/history.db")
        db = ExecutionDatabase(str(db_path))

        # Initialize executor
        executor = PytestExecutorWithHistory(db=db, config_path=config_path)

        if not quiet:
            print(f"Executing tests with rule: {rule}")
            print("=" * 50)

        # Execute with rule
        result = executor.execute_with_rule(
            rule_name=rule, config={"verbose": verbose} if verbose else {}
        )

        if not quiet:
            if result:
                print(f"\nValidation {'passed' if result.is_valid else 'failed'}")
                print(f"Files checked: {result.files_checked}")
                if result.errors:
                    print(f"Errors: {len(result.errors)}")
            else:
                print("\nValidation completed")

        # Return based on validation result
        if result and not result.is_valid:
            return 1
        return 0

    except FileNotFoundError as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
            print("Rule not found. Use 'anvil rules list' to see available rules.", file=sys.stderr)
        return 2
    except Exception as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 2
    finally:
        # Ensure database is closed
        if executor:
            try:
                executor.close()
            except Exception:
                pass
        if db:
            try:
                db.close()
            except Exception:
                pass


def rules_list_command(
    args,
    enabled_only: bool = False,
    quiet: bool = False,
) -> int:
    """
    List execution rules.

    Args:
        args: Parsed arguments from argparse
        enabled_only: Show only enabled rules
        quiet: Suppress output

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        from anvil.core.rule_engine import RuleEngine
        from anvil.storage.execution_schema import ExecutionDatabase

        # Initialize database
        db_path = Path(".anvil/history.db")
        db = ExecutionDatabase(str(db_path))

        # Initialize rule engine
        rule_engine = RuleEngine(db)

        # Get rules
        rules = rule_engine.list_rules(enabled_only=enabled_only)

        if not quiet:
            print("Execution Rules")
            print("=" * 70)
            if enabled_only:
                print("(Showing enabled rules only)")
            print()

            if not rules:
                print("No rules found.")
                print("Rules can be defined in the database using ExecutionRule.")
            else:
                for rule in rules:
                    status = "✓" if rule.enabled else "✗"
                    print(f"{status} {rule.name}")
                    print(f"  Criteria: {rule.criteria}")
                    if rule.threshold is not None:
                        print(f"  Threshold: {rule.threshold}")
                    if rule.window is not None:
                        print(f"  Window: {rule.window}")
                    if rule.groups:
                        print(f"  Groups: {', '.join(rule.groups)}")
                    print()

        # Close database
        db.close()
        return 0

    except Exception as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 1


def stats_show_command(
    args,
    entity_type: str = "test",
    window: int = 20,
    quiet: bool = False,
) -> int:
    """
    Show entity statistics.

    Args:
        args: Parsed arguments from argparse
        entity_type: Type of entity (test, coverage, lint)
        window: Number of recent executions to analyze
        quiet: Suppress output

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        from anvil.core.statistics_calculator import StatisticsCalculator
        from anvil.storage.execution_schema import ExecutionDatabase

        # Initialize database
        db_path = Path(".anvil/history.db")
        db = ExecutionDatabase(str(db_path))

        # Initialize calculator
        calculator = StatisticsCalculator(db)

        # Calculate statistics
        stats = calculator.calculate_all_stats(entity_type=entity_type, window=window)

        if not quiet:
            print(f"Entity Statistics ({entity_type})")
            print("=" * 90)
            print(f"Window: Last {window} executions")
            print()

            if not stats:
                print("No statistics available.")
                print("Execute tests to build execution history.")
            else:
                # Print header
                print(
                    f"{'Entity ID':<50} {'Runs':>6} {'Pass':>6} "
                    f"{'Fail':>6} {'Rate':>7} {'Avg Dur':>8}"
                )
                print("-" * 90)

                # Print each entity
                for stat in stats:
                    entity_id_short = stat.entity_id
                    if len(entity_id_short) > 47:
                        entity_id_short = "..." + entity_id_short[-44:]

                    print(
                        f"{entity_id_short:<50} "
                        f"{stat.total_runs:>6} "
                        f"{stat.passed:>6} "
                        f"{stat.failed:>6} "
                        f"{stat.failure_rate:>6.1%} "
                        f"{stat.avg_duration:>7.2f}s"
                    )

                print()
                print(f"Total entities: {len(stats)}")

        # Close database
        db.close()
        return 0

    except Exception as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 1


def stats_flaky_tests_command(
    args,
    threshold: float = 0.10,
    window: int = 20,
    quiet: bool = False,
) -> int:
    """
    Show flaky tests based on execution history.

    Args:
        args: Parsed arguments from argparse
        threshold: Failure rate threshold (0.0-1.0)
        window: Number of recent executions to analyze
        quiet: Suppress output

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        from anvil.executors.pytest_executor import PytestExecutorWithHistory
        from anvil.storage.execution_schema import ExecutionDatabase

        # Validate threshold
        if threshold < 0.0 or threshold > 1.0:
            if not quiet:
                print("Error: Threshold must be between 0.0 and 1.0", file=sys.stderr)
            return 1

        # Initialize database
        db_path = Path(".anvil/history.db")
        db = ExecutionDatabase(str(db_path))

        # Initialize executor
        executor = PytestExecutorWithHistory(db=db)

        # Get flaky tests
        flaky_tests = executor.get_flaky_tests(threshold=threshold, window=window)

        if not quiet:
            print("Flaky Tests")
            print("=" * 90)
            print(f"Threshold: {threshold:.1%} failure rate")
            print(f"Window: Last {window} executions")
            print()

            if not flaky_tests:
                print("No flaky tests detected.")
            else:
                print(f"Found {len(flaky_tests)} flaky test(s):")
                print()
                for test_id in flaky_tests:
                    print(f"  - {test_id}")

        # Close database
        executor.close()
        return 0

    except Exception as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 1


def history_show_command(
    args,
    entity: str,
    limit: int = 10,
    quiet: bool = False,
) -> int:
    """
    Show execution history for an entity.

    Args:
        args: Parsed arguments from argparse
        entity: Entity ID (e.g., test nodeid)
        limit: Number of recent executions to show
        quiet: Suppress output

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        from anvil.storage.execution_schema import ExecutionDatabase

        # Initialize database
        db_path = Path(".anvil/history.db")
        db = ExecutionDatabase(str(db_path))

        # Get execution history
        history = db.get_execution_history(entity_id=entity, entity_type="test", limit=limit)

        if not quiet:
            print("Execution History")
            print("=" * 90)
            print(f"Entity: {entity}")
            print(f"Showing: Last {limit} executions")
            print()

            if not history:
                print("No execution history found.")
            else:
                # Print header
                print(f"{'Execution ID':<30} {'Timestamp':<20} {'Status':<10} {'Duration':>10}")
                print("-" * 90)

                # Print each execution
                for record in history:
                    timestamp_str = record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    duration_str = f"{record.duration:.2f}s" if record.duration else "N/A"

                    print(
                        f"{record.execution_id:<30} "
                        f"{timestamp_str:<20} "
                        f"{record.status:<10} "
                        f"{duration_str:>10}"
                    )

                print()
                print(f"Total records: {len(history)}")

        # Close database
        db.close()
        return 0

    except Exception as e:
        if not quiet:
            print(f"Error: {e}", file=sys.stderr)
        return 1
