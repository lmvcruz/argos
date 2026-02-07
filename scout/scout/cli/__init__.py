"""
Scout CLI package with command modules.

Provides command handlers for fetch, parse, and sync operations.
"""

import importlib.util
from pathlib import Path

from scout.cli.fetch_commands import (
    handle_fetch_all_command,
    handle_fetch_command,
    handle_fetch_last_command,
)
from scout.cli.parse_commands import (
    handle_parse_from_db_command,
    handle_parse_from_file_command,
)
from scout.cli.sync_commands import handle_sync_command

# Load scout/cli.py module directly to avoid package shadowing
# This allows code to import create_parser and main from scout.cli
_cli_py_path = Path(__file__).parent.parent / "cli.py"
_spec = importlib.util.spec_from_file_location("_scout_cli_original", _cli_py_path)
if _spec and _spec.loader:
    _cli_original = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_cli_original)

    # Re-export the original functions and classes
    create_parser = _cli_original.create_parser
    main = _cli_original.main
    Config = _cli_original.Config
    AnalysisEngine = _cli_original.AnalysisEngine
    ConsoleReporter = _cli_original.ConsoleReporter
    HtmlReporter = _cli_original.HtmlReporter
    FailureParser = _cli_original.FailureParser
    GitHubActionsProvider = _cli_original.GitHubActionsProvider
    LogRetriever = _cli_original.LogRetriever
    handle_fetch_command_v2 = _cli_original.handle_fetch_command_v2
    handle_parse_command_v2 = _cli_original.handle_parse_command_v2
    get_github_credentials = _cli_original.get_github_credentials
    get_repo_data_manager = _cli_original.get_repo_data_manager
    get_db_path = _cli_original.get_db_path

__all__ = [
    "create_parser",
    "main",
    "Config",
    "AnalysisEngine",
    "ConsoleReporter",
    "HtmlReporter",
    "FailureParser",
    "GitHubActionsProvider",
    "LogRetriever",
    "handle_fetch_command",
    "handle_fetch_all_command",
    "handle_fetch_last_command",
    "handle_fetch_command_v2",
    "handle_parse_from_file_command",
    "handle_parse_from_db_command",
    "handle_parse_command_v2",
    "handle_sync_command",
    "get_github_credentials",
    "get_repo_data_manager",
    "get_db_path",
    "handle_sync_command",
]
