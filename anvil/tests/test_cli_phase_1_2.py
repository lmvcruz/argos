"""
Tests for Phase 1.2.5 CLI commands.

This module tests the new CLI commands for selective execution:
- execute: Run tests with a rule
- rules list: List execution rules
- stats show: Show entity statistics
- stats flaky-tests: Show flaky tests
- history show: Show execution history
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from anvil.cli.commands import (
    execute_command,
    history_show_command,
    rules_list_command,
    stats_flaky_tests_command,
    stats_show_command,
)
from anvil.core.statistics_calculator import StatisticsCalculator
from anvil.storage.execution_schema import (
    ExecutionDatabase,
    ExecutionHistory,
    ExecutionRule,
)


class MockArgs:
    """Mock argparse arguments."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / ".anvil" / "history.db"
        db = ExecutionDatabase(str(db_path))
        yield db
        db.close()


@pytest.fixture
def populated_db(temp_db):
    """Create a database with sample data."""
    # Add execution rules
    rule1 = ExecutionRule(
        name="quick-check",
        criteria="group",
        enabled=True,
        groups=["tests/test_models.py", "tests/test_parser.py"],
    )
    rule2 = ExecutionRule(
        name="failed-tests",
        criteria="failed-in-last",
        enabled=True,
        window=1,
    )
    rule3 = ExecutionRule(
        name="disabled-rule",
        criteria="all",
        enabled=False,
    )

    temp_db.insert_execution_rule(rule1)
    temp_db.insert_execution_rule(rule2)
    temp_db.insert_execution_rule(rule3)

    # Add execution history
    base_time = datetime.now()
    for i in range(10):
        # Test that always passes
        history1 = ExecutionHistory(
            execution_id=f"test-{i}",
            entity_id="tests/test_stable.py::test_always_passes",
            entity_type="test",
            timestamp=base_time - timedelta(hours=i),
            status="PASSED",
            duration=1.0,
            space="local",
        )
        temp_db.insert_execution_history(history1)

        # Flaky test (50% failure rate)
        status = "PASSED" if i % 2 == 0 else "FAILED"
        history2 = ExecutionHistory(
            execution_id=f"test-{i}",
            entity_id="tests/test_flaky.py::test_sometimes_fails",
            entity_type="test",
            timestamp=base_time - timedelta(hours=i),
            status=status,
            duration=2.0,
            space="local",
        )
        temp_db.insert_execution_history(history2)

    # Update statistics
    calculator = StatisticsCalculator(temp_db)
    stats1 = calculator.calculate_entity_stats(
        "tests/test_stable.py::test_always_passes", window=10
    )
    stats2 = calculator.calculate_entity_stats(
        "tests/test_flaky.py::test_sometimes_fails", window=10
    )

    if stats1:
        temp_db.update_entity_statistics(stats1)
    if stats2:
        temp_db.update_entity_statistics(stats2)

    return temp_db


class TestRulesListCommand:
    """Test the 'rules list' command."""

    def test_list_all_rules(self, populated_db, monkeypatch, capsys):
        """Test listing all rules."""
        # Change working directory to temp db location
        db_dir = Path(populated_db.db_path).parent.parent
        monkeypatch.chdir(db_dir)

        args = MockArgs()
        result = rules_list_command(args, enabled_only=False, quiet=False)

        assert result == 0

        captured = capsys.readouterr()
        assert "quick-check" in captured.out
        assert "failed-tests" in captured.out
        assert "disabled-rule" in captured.out

    def test_list_enabled_only(self, populated_db, monkeypatch, capsys):
        """Test listing enabled rules only."""
        db_dir = Path(populated_db.db_path).parent.parent
        monkeypatch.chdir(db_dir)

        args = MockArgs()
        result = rules_list_command(args, enabled_only=True, quiet=False)

        assert result == 0

        captured = capsys.readouterr()
        assert "quick-check" in captured.out
        assert "failed-tests" in captured.out
        assert "disabled-rule" not in captured.out

    def test_quiet_mode(self, populated_db, monkeypatch, capsys):
        """Test quiet mode suppresses output."""
        db_dir = Path(populated_db.db_path).parent.parent
        monkeypatch.chdir(db_dir)

        args = MockArgs()
        result = rules_list_command(args, enabled_only=False, quiet=True)

        assert result == 0

        captured = capsys.readouterr()
        assert captured.out == ""


class TestStatsShowCommand:
    """Test the 'stats show' command."""

    def test_show_test_statistics(self, populated_db, monkeypatch, capsys):
        """Test showing test statistics."""
        db_dir = Path(populated_db.db_path).parent.parent
        monkeypatch.chdir(db_dir)

        args = MockArgs()
        result = stats_show_command(args, entity_type="test", window=10, quiet=False)

        assert result == 0

        captured = capsys.readouterr()
        assert "test_always_passes" in captured.out
        assert "test_sometimes_fails" in captured.out

    def test_quiet_mode(self, populated_db, monkeypatch, capsys):
        """Test quiet mode suppresses output."""
        db_dir = Path(populated_db.db_path).parent.parent
        monkeypatch.chdir(db_dir)

        args = MockArgs()
        result = stats_show_command(args, entity_type="test", window=10, quiet=True)

        assert result == 0

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_empty_database(self, temp_db, monkeypatch, capsys):
        """Test with empty database."""
        db_dir = Path(temp_db.db_path).parent.parent
        monkeypatch.chdir(db_dir)

        args = MockArgs()
        result = stats_show_command(args, entity_type="test", window=10, quiet=False)

        assert result == 0

        captured = capsys.readouterr()
        assert "No statistics available" in captured.out


class TestStatsFlakyTestsCommand:
    """Test the 'stats flaky-tests' command."""

    def test_detect_flaky_tests(self, populated_db, monkeypatch, capsys):
        """Test detecting flaky tests."""
        db_dir = Path(populated_db.db_path).parent.parent
        monkeypatch.chdir(db_dir)

        args = MockArgs()
        # Threshold 0.10 means 10% failure rate or higher
        result = stats_flaky_tests_command(args, threshold=0.10, window=10, quiet=False)

        assert result == 0

        captured = capsys.readouterr()
        # Flaky test should be detected (50% failure rate > 10% threshold)
        assert "test_sometimes_fails" in captured.out
        # Stable test should not be detected (0% failure rate < 10% threshold)
        assert "test_always_passes" not in captured.out

    def test_no_flaky_tests(self, populated_db, monkeypatch, capsys):
        """Test when no flaky tests are found."""
        db_dir = Path(populated_db.db_path).parent.parent
        monkeypatch.chdir(db_dir)

        args = MockArgs()
        # High threshold means only very flaky tests are detected
        result = stats_flaky_tests_command(args, threshold=0.90, window=10, quiet=False)

        assert result == 0

        captured = capsys.readouterr()
        assert "No flaky tests detected" in captured.out

    def test_invalid_threshold(self, populated_db, monkeypatch, capsys):
        """Test with invalid threshold."""
        db_dir = Path(populated_db.db_path).parent.parent
        monkeypatch.chdir(db_dir)

        args = MockArgs()
        result = stats_flaky_tests_command(args, threshold=1.5, window=10, quiet=False)

        assert result == 1

        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_quiet_mode(self, populated_db, monkeypatch, capsys):
        """Test quiet mode suppresses output."""
        db_dir = Path(populated_db.db_path).parent.parent
        monkeypatch.chdir(db_dir)

        args = MockArgs()
        result = stats_flaky_tests_command(args, threshold=0.10, window=10, quiet=True)

        assert result == 0

        captured = capsys.readouterr()
        assert captured.out == ""


class TestHistoryShowCommand:
    """Test the 'history show' command."""

    def test_show_execution_history(self, populated_db, monkeypatch, capsys):
        """Test showing execution history."""
        db_dir = Path(populated_db.db_path).parent.parent
        monkeypatch.chdir(db_dir)

        args = MockArgs()
        result = history_show_command(
            args,
            entity="tests/test_stable.py::test_always_passes",
            limit=5,
            quiet=False,
        )

        assert result == 0

        captured = capsys.readouterr()
        assert "test_always_passes" in captured.out
        assert "PASSED" in captured.out

    def test_entity_not_found(self, populated_db, monkeypatch, capsys):
        """Test with non-existent entity."""
        db_dir = Path(populated_db.db_path).parent.parent
        monkeypatch.chdir(db_dir)

        args = MockArgs()
        result = history_show_command(
            args,
            entity="tests/test_nonexistent.py::test_missing",
            limit=10,
            quiet=False,
        )

        assert result == 0

        captured = capsys.readouterr()
        assert "No execution history found" in captured.out

    def test_quiet_mode(self, populated_db, monkeypatch, capsys):
        """Test quiet mode suppresses output."""
        db_dir = Path(populated_db.db_path).parent.parent
        monkeypatch.chdir(db_dir)

        args = MockArgs()
        result = history_show_command(
            args,
            entity="tests/test_stable.py::test_always_passes",
            limit=5,
            quiet=True,
        )

        assert result == 0

        captured = capsys.readouterr()
        assert captured.out == ""


class TestExecuteCommand:
    """Test the 'execute' command."""

    def test_rule_not_found(self, temp_db, monkeypatch, capsys):
        """Test executing with non-existent rule."""
        db_dir = Path(temp_db.db_path).parent.parent
        monkeypatch.chdir(db_dir)

        args = MockArgs(config_path=None, execution_id=None)
        result = execute_command(
            args,
            rule="nonexistent-rule",
            config_path=None,
            execution_id=None,
            verbose=False,
            quiet=False,
        )

        assert result == 2

        captured = capsys.readouterr()
        assert "Error" in captured.err or "not found" in captured.err.lower()

    def test_quiet_mode_with_error(self, temp_db, monkeypatch, capsys):
        """Test quiet mode with error."""
        db_dir = Path(temp_db.db_path).parent.parent
        monkeypatch.chdir(db_dir)

        args = MockArgs(config_path=None, execution_id=None)
        result = execute_command(
            args,
            rule="nonexistent-rule",
            config_path=None,
            execution_id=None,
            verbose=False,
            quiet=True,
        )

        assert result == 2

        captured = capsys.readouterr()
        assert captured.out == ""
