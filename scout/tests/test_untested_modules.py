"""
Placeholder tests for untested modules.

These tests import modules that have 0% coverage to establish basic coverage.
"""

from scout.ci.parser_resolver import ParserConfig
from scout.ci.sync import SyncResult
from scout.ci.sync_output import SyncOutputFormatter
from scout.new_parser import create_new_parser


def test_parser_config_creation():
    """Test ParserConfig dataclass creation."""
    config = ParserConfig(pattern="test", parser="pytest")
    assert config.pattern == "test"
    assert config.parser == "pytest"
    assert config.get_parser_names() == ["pytest"]


def test_parser_config_multiple_parsers():
    """Test ParserConfig with multiple parsers."""
    config = ParserConfig(pattern="test", parsers=["pytest", "unittest"])
    assert config.get_parser_names() == ["pytest", "unittest"]


def test_sync_result_creation():
    """Test SyncResult dataclass creation."""
    result = SyncResult(downloaded_count=5, skipped_download_count=3)
    assert result.downloaded_count == 5
    assert result.skipped_download_count == 3
    assert result.total_jobs_processed == 8


def test_sync_output_formatter_colors():
    """Test SyncOutputFormatter color codes."""
    formatter = SyncOutputFormatter()
    assert formatter.GREEN == "\033[92m"
    assert formatter.RED == "\033[91m"
    assert formatter.RESET == "\033[0m"


def test_create_new_parser():
    """Test creation of new argument parser."""
    parser = create_new_parser()
    assert parser is not None
    assert parser.prog == "scout"
