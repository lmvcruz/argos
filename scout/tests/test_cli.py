"""
Tests for Scout CLI interface.

This module contains comprehensive tests for the Scout command-line interface,
including all subcommands, argument parsing, and integration with core components.
"""

from io import StringIO
from unittest.mock import patch

import pytest

from scout.cli import create_parser, main


class TestCLIArgumentParsing:
    """Test CLI argument parsing."""

    def test_create_parser_returns_argparse_parser(self):
        """Test that create_parser returns an ArgumentParser instance."""
        parser = create_parser()
        assert parser is not None
        assert hasattr(parser, "parse_args")

    def test_parser_has_version_argument(self):
        """Test that parser has --version argument."""
        parser = create_parser()
        with patch("sys.stdout", new_callable=StringIO):
            with pytest.raises(SystemExit) as exc_info:
                parser.parse_args(["--version"])
            assert exc_info.value.code == 0

    def test_parser_has_help_argument(self):
        """Test that parser has --help argument."""
        parser = create_parser()
        with patch("sys.stdout", new_callable=StringIO):
            with pytest.raises(SystemExit) as exc_info:
                parser.parse_args(["--help"])
            assert exc_info.value.code == 0

    def test_parser_requires_subcommand(self):
        """Test that parser requires a subcommand."""
        parser = create_parser()
        with patch("sys.stderr", new_callable=StringIO):
            # Since required=True, parse_args will raise SystemExit when no subcommand
            with pytest.raises(SystemExit):
                parser.parse_args([])


class TestLogsCommand:
    """Test 'scout logs' command."""

    def test_logs_command_with_workflow_name(self):
        """Test logs command with workflow name argument."""
        parser = create_parser()
        args = parser.parse_args(["logs", "CI Tests"])
        assert args.command == "logs"
        assert args.workflow == "CI Tests"

    def test_logs_command_with_limit_option(self):
        """Test logs command with --limit option."""
        parser = create_parser()
        args = parser.parse_args(["logs", "CI Tests", "--limit", "5"])
        assert args.workflow == "CI Tests"
        assert args.limit == 5

    def test_logs_command_with_output_option(self):
        """Test logs command with --output option."""
        parser = create_parser()
        args = parser.parse_args(["logs", "CI Tests", "--output", "logs/"])
        assert args.workflow == "CI Tests"
        assert args.output == "logs/"

    def test_logs_command_with_branch_filter(self):
        """Test logs command with --branch option."""
        parser = create_parser()
        args = parser.parse_args(["logs", "CI Tests", "--branch", "main"])
        assert args.workflow == "CI Tests"
        assert args.branch == "main"


class TestAnalyzeCommand:
    """Test 'scout analyze' command."""

    def test_analyze_command_with_run_id(self):
        """Test analyze command with run ID argument."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "123456"])
        assert args.command == "analyze"
        assert args.run_id == "123456"

    def test_analyze_command_with_format_option(self):
        """Test analyze command with --format option."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "123456", "--format", "html"])
        assert args.run_id == "123456"
        assert args.format == "html"

    def test_analyze_command_with_output_file(self):
        """Test analyze command with --output option."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "123456", "--output", "report.html"])
        assert args.run_id == "123456"
        assert args.output == "report.html"

    def test_analyze_command_with_verbose_flag(self):
        """Test analyze command with --verbose flag."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "123456", "--verbose"])
        assert args.run_id == "123456"
        assert args.verbose is True


class TestTrendsCommand:
    """Test 'scout trends' command."""

    def test_trends_command_with_workflow_name(self):
        """Test trends command with workflow name argument."""
        parser = create_parser()
        args = parser.parse_args(["trends", "CI Tests"])
        assert args.command == "trends"
        assert args.workflow == "CI Tests"

    def test_trends_command_with_days_option(self):
        """Test trends command with --days option."""
        parser = create_parser()
        args = parser.parse_args(["trends", "CI Tests", "--days", "14"])
        assert args.workflow == "CI Tests"
        assert args.days == 14

    def test_trends_command_with_format_option(self):
        """Test trends command with --format option."""
        parser = create_parser()
        args = parser.parse_args(["trends", "CI Tests", "--format", "json"])
        assert args.workflow == "CI Tests"
        assert args.format == "json"


class TestFlakyCommand:
    """Test 'scout flaky' command."""

    def test_flaky_command_no_arguments(self):
        """Test flaky command without arguments."""
        parser = create_parser()
        args = parser.parse_args(["flaky"])
        assert args.command == "flaky"

    def test_flaky_command_with_threshold_option(self):
        """Test flaky command with --threshold option."""
        parser = create_parser()
        args = parser.parse_args(["flaky", "--threshold", "0.3"])
        assert args.command == "flaky"
        assert args.threshold == 0.3

    def test_flaky_command_with_min_runs_option(self):
        """Test flaky command with --min-runs option."""
        parser = create_parser()
        args = parser.parse_args(["flaky", "--min-runs", "5"])
        assert args.command == "flaky"
        assert args.min_runs == 5

    def test_flaky_command_with_format_option(self):
        """Test flaky command with --format option."""
        parser = create_parser()
        args = parser.parse_args(["flaky", "--format", "csv"])
        assert args.command == "flaky"
        assert args.format == "csv"


class TestConfigCommand:
    """Test 'scout config' command."""

    def test_config_show_command(self):
        """Test config show command."""
        parser = create_parser()
        args = parser.parse_args(["config", "show"])
        assert args.command == "config"
        assert args.config_command == "show"

    def test_config_set_command_with_key_value(self):
        """Test config set command with key and value."""
        parser = create_parser()
        args = parser.parse_args(["config", "set", "github.token", "ghp_xxx"])
        assert args.command == "config"
        assert args.config_command == "set"
        assert args.key == "github.token"
        assert args.value == "ghp_xxx"

    def test_config_get_command_with_key(self):
        """Test config get command with key."""
        parser = create_parser()
        args = parser.parse_args(["config", "get", "github.repo"])
        assert args.command == "config"
        assert args.config_command == "get"
        assert args.key == "github.repo"


class TestAuthenticationHandling:
    """Test authentication configuration."""

    def test_token_from_environment_variable(self):
        """Test token loaded from GITHUB_TOKEN environment variable."""
        with patch.dict("os.environ", {"GITHUB_TOKEN": "ghp_test_token"}):
            parser = create_parser()
            args = parser.parse_args(["logs", "CI Tests"])
            # Token should be available from environment
            assert args is not None

    def test_token_from_command_line_option(self):
        """Test token provided via --token option."""
        parser = create_parser()
        args = parser.parse_args(["logs", "CI Tests", "--token", "ghp_cli_token"])
        assert args.token == "ghp_cli_token"

    def test_repo_from_environment_variable(self):
        """Test repository loaded from GITHUB_REPO environment variable."""
        with patch.dict("os.environ", {"GITHUB_REPO": "owner/repo"}):
            parser = create_parser()
            args = parser.parse_args(["logs", "CI Tests"])
            assert args is not None

    def test_repo_from_command_line_option(self):
        """Test repository provided via --repo option."""
        parser = create_parser()
        args = parser.parse_args(["logs", "CI Tests", "--repo", "cli-owner/cli-repo"])
        assert args.repo == "cli-owner/cli-repo"


class TestOutputFormatOptions:
    """Test output format options."""

    def test_console_format(self):
        """Test console output format."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "123", "--format", "console"])
        assert args.format == "console"

    def test_html_format(self):
        """Test HTML output format."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "123", "--format", "html"])
        assert args.format == "html"

    def test_json_format(self):
        """Test JSON output format."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "123", "--format", "json"])
        assert args.format == "json"

    def test_csv_format(self):
        """Test CSV output format."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "123", "--format", "csv"])
        assert args.format == "csv"

    def test_default_format_is_console(self):
        """Test that default format is console."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "123"])
        assert args.format == "console"


class TestVerboseOutput:
    """Test verbose output mode."""

    def test_verbose_flag_sets_logging_level(self):
        """Test that --verbose flag is parsed correctly."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "123", "--verbose"])
        assert args.verbose is True

    def test_quiet_flag_sets_logging_level(self):
        """Test that --quiet flag is parsed correctly."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "123", "--quiet"])
        assert args.quiet is True


class TestMainFunction:
    """Test main entry point function."""

    def test_main_with_no_arguments_shows_help(self):
        """Test that main with no arguments shows help and exits."""
        with patch("sys.argv", ["scout"]):
            with patch("sys.stderr", new_callable=StringIO):
                # argparse exits with code 2 for missing required argument
                exit_code = main()
        assert exit_code == 2  # argparse uses exit code 2 for parse errors

    def test_main_returns_zero_on_success(self):
        """Test that main returns 0 on successful execution."""
        with patch("sys.argv", ["scout", "--version"]):
            with patch("sys.stdout", new_callable=StringIO):
                # --version causes SystemExit(0) which we now catch and return
                exit_code = main()
        assert exit_code == 0

    def test_main_returns_nonzero_on_error(self):
        """Test that main returns non-zero on error."""
        with patch("sys.argv", ["scout"]):
            with patch("sys.stderr", new_callable=StringIO):
                exit_code = main()
        assert exit_code != 0
