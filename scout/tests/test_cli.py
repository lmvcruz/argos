"""
Tests for Scout CLI interface.

This module contains comprehensive tests for the Scout command-line interface,
including all subcommands, argument parsing, and integration with core components.
"""

from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

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

    @patch("scout.cli.GitHubActionsProvider")
    @patch("scout.cli.LogRetriever")
    def test_logs_command_execution(self, mock_retriever, mock_provider):
        """Test execution of logs command."""
        mock_provider_instance = MagicMock()
        mock_provider.return_value = mock_provider_instance
        mock_retriever_instance = MagicMock()
        mock_retriever.return_value = mock_retriever_instance

        with patch("sys.argv", ["scout", "logs", "CI Tests", "--limit", "3"]):
            with patch.dict(
                "os.environ", {"GITHUB_TOKEN": "test-token", "GITHUB_REPO": "owner/repo"}
            ):
                exit_code = main()

        assert exit_code == 0
        mock_retriever_instance.retrieve_logs.assert_called_once()


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

    @patch("scout.cli.GitHubActionsProvider")
    @patch("scout.cli.LogRetriever")
    @patch("scout.cli.FailureParser")
    @patch("scout.cli.AnalysisEngine")
    @patch("scout.cli.ConsoleReporter")
    def test_analyze_command_execution(
        self, mock_reporter, mock_engine, mock_parser, mock_retriever, mock_provider
    ):
        """Test execution of analyze command."""
        # Setup mocks
        mock_provider_instance = MagicMock()
        mock_provider.return_value = mock_provider_instance
        mock_retriever_instance = MagicMock()
        mock_retriever.return_value = mock_retriever_instance
        mock_parser_instance = MagicMock()
        mock_parser.return_value = mock_parser_instance
        mock_engine_instance = MagicMock()
        mock_engine.return_value = mock_engine_instance
        mock_reporter_instance = MagicMock()
        mock_reporter.return_value = mock_reporter_instance

        # Configure mocks to return test data
        mock_retriever_instance.get_logs.return_value = "test log content"
        mock_parser_instance.parse.return_value = []
        mock_engine_instance.analyze.return_value = MagicMock()
        mock_reporter_instance.generate_report.return_value = "Test Report"

        with patch("sys.argv", ["scout", "analyze", "123456"]):
            with patch.dict(
                "os.environ", {"GITHUB_TOKEN": "test-token", "GITHUB_REPO": "owner/repo"}
            ):
                exit_code = main()

        assert exit_code == 0
        mock_engine_instance.analyze.assert_called_once()
        mock_reporter_instance.generate_report.assert_called_once()


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

    @patch("scout.cli.GitHubActionsProvider")
    @patch("scout.cli.LogRetriever")
    @patch("scout.cli.AnalysisEngine")
    def test_trends_command_execution(self, mock_engine, mock_retriever, mock_provider):
        """Test execution of trends command."""
        mock_provider_instance = MagicMock()
        mock_provider.return_value = mock_provider_instance
        mock_retriever_instance = MagicMock()
        mock_retriever.return_value = mock_retriever_instance
        mock_engine_instance = MagicMock()
        mock_engine.return_value = mock_engine_instance

        # Configure mocks
        mock_retriever_instance.retrieve_logs.return_value = []
        mock_engine_instance.analyze_trends.return_value = MagicMock()

        with patch("sys.argv", ["scout", "trends", "CI Tests", "--days", "7"]):
            with patch.dict(
                "os.environ", {"GITHUB_TOKEN": "test-token", "GITHUB_REPO": "owner/repo"}
            ):
                exit_code = main()

        assert exit_code == 0
        mock_engine_instance.analyze_trends.assert_called_once()


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

    @patch("scout.cli.AnalysisEngine")
    def test_flaky_command_execution(self, mock_engine):
        """Test execution of flaky command."""
        mock_engine_instance = MagicMock()
        mock_engine.return_value = mock_engine_instance

        # Configure mock to return flaky test results
        mock_engine_instance.detect_flaky_tests.return_value = []

        with patch("sys.argv", ["scout", "flaky", "--threshold", "0.2"]):
            with patch.dict(
                "os.environ", {"GITHUB_TOKEN": "test-token", "GITHUB_REPO": "owner/repo"}
            ):
                exit_code = main()

        assert exit_code == 0
        mock_engine_instance.detect_flaky_tests.assert_called_once()


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

    @patch("scout.cli.Config")
    def test_config_show_execution(self, mock_config):
        """Test execution of config show command."""
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        mock_config_instance.get_all.return_value = {
            "github": {"owner": "test-owner", "repo": "test-repo"}
        }

        with patch("sys.argv", ["scout", "config", "show"]):
            exit_code = main()

        assert exit_code == 0
        mock_config_instance.get_all.assert_called_once()


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


class TestErrorHandling:
    """Test error handling in CLI."""

    @patch("scout.cli.GitHubActionsProvider")
    def test_missing_token_error(self, mock_provider):
        """Test error when GitHub token is missing."""
        mock_provider.side_effect = ValueError("GitHub token required")

        with patch("sys.argv", ["scout", "logs", "CI Tests"]):
            with patch.dict("os.environ", {}, clear=True):
                exit_code = main()

        assert exit_code != 0

    @patch("scout.cli.GitHubActionsProvider")
    def test_invalid_repository_format_error(self, mock_provider):
        """Test error when repository format is invalid."""
        mock_provider.side_effect = ValueError("Invalid repository format")

        with patch("sys.argv", ["scout", "logs", "CI Tests", "--repo", "invalid"]):
            with patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}):
                exit_code = main()

        assert exit_code != 0

    @patch("scout.cli.GitHubActionsProvider")
    @patch("scout.cli.LogRetriever")
    def test_network_error_handling(self, mock_retriever, mock_provider):
        """Test handling of network errors."""
        mock_provider_instance = MagicMock()
        mock_provider.return_value = mock_provider_instance
        mock_retriever_instance = MagicMock()
        mock_retriever.return_value = mock_retriever_instance
        mock_retriever_instance.retrieve_logs.side_effect = ConnectionError("Network error")

        with patch("sys.argv", ["scout", "logs", "CI Tests"]):
            with patch.dict(
                "os.environ", {"GITHUB_TOKEN": "test-token", "GITHUB_REPO": "owner/repo"}
            ):
                exit_code = main()

        assert exit_code != 0


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


class TestCLIIntegration:
    """Integration tests for CLI."""

    @patch("scout.cli.GitHubActionsProvider")
    @patch("scout.cli.LogRetriever")
    @patch("scout.cli.FailureParser")
    @patch("scout.cli.AnalysisEngine")
    @patch("scout.cli.ConsoleReporter")
    def test_full_analyze_workflow(
        self, mock_reporter, mock_engine, mock_parser, mock_retriever, mock_provider
    ):
        """Test complete analyze workflow from CLI to report."""
        # Setup comprehensive mocks
        mock_provider_instance = MagicMock()
        mock_provider.return_value = mock_provider_instance
        mock_retriever_instance = MagicMock()
        mock_retriever.return_value = mock_retriever_instance
        mock_parser_instance = MagicMock()
        mock_parser.return_value = mock_parser_instance
        mock_engine_instance = MagicMock()
        mock_engine.return_value = mock_engine_instance
        mock_reporter_instance = MagicMock()
        mock_reporter.return_value = mock_reporter_instance

        # Configure mock returns
        mock_retriever_instance.get_logs.return_value = "test log content"
        mock_parser_instance.parse.return_value = [
            MagicMock(test_name="test_example", message="Failed")
        ]
        mock_engine_instance.analyze.return_value = MagicMock(
            failures=[], flaky_tests=[], recommendations=[]
        )
        mock_reporter_instance.generate_report.return_value = "Analysis Report"

        with patch("sys.argv", ["scout", "analyze", "123456"]):
            with patch.dict(
                "os.environ", {"GITHUB_TOKEN": "test-token", "GITHUB_REPO": "owner/repo"}
            ):
                exit_code = main()

        assert exit_code == 0
        # Verify all components were called
        mock_retriever_instance.get_logs.assert_called_once()
        mock_parser_instance.parse.assert_called_once()
        mock_engine_instance.analyze.assert_called_once()
        mock_reporter_instance.generate_report.assert_called_once()

    @patch("scout.cli.GitHubActionsProvider")
    @patch("scout.cli.LogRetriever")
    @patch("scout.cli.HtmlReporter")
    def test_html_report_generation_workflow(self, mock_reporter, mock_retriever, mock_provider):
        """Test HTML report generation workflow."""
        mock_provider_instance = MagicMock()
        mock_provider.return_value = mock_provider_instance
        mock_retriever_instance = MagicMock()
        mock_retriever.return_value = mock_retriever_instance
        mock_reporter_instance = MagicMock()
        mock_reporter.return_value = mock_reporter_instance

        mock_reporter_instance.generate_report.return_value = "<html>Report</html>"
        mock_reporter_instance.save.return_value = None

        with patch(
            "sys.argv", ["scout", "analyze", "123", "--format", "html", "--output", "report.html"]
        ):
            with patch.dict(
                "os.environ", {"GITHUB_TOKEN": "test-token", "GITHUB_REPO": "owner/repo"}
            ):
                # Need to mock additional components
                with patch("scout.cli.FailureParser"):
                    with patch("scout.cli.AnalysisEngine"):
                        exit_code = main()

        assert exit_code == 0


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
