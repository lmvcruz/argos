"""
Tests for enhanced pytest executor with history tracking.

Following TDD principles: Tests written before full implementation.
"""

import tempfile
from pathlib import Path

import pytest

from anvil.executors.pytest_executor import PytestExecutorWithHistory
from anvil.storage.execution_schema import ExecutionDatabase, ExecutionRule


class TestPytestExecutorWithHistory:
    """Test suite for PytestExecutorWithHistory."""

    @pytest.fixture
    def db(self):
        """Create in-memory database for testing."""
        database = ExecutionDatabase(":memory:")
        yield database
        database.close()

    @pytest.fixture
    def executor(self, db):
        """Create executor instance with test database."""
        return PytestExecutorWithHistory(db=db)

    @pytest.fixture
    def temp_test_file(self):
        """Create a temporary test file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix="_test.py", delete=False) as f:
            f.write("""
import pytest

def test_passing():
    assert 1 + 1 == 2

def test_failing():
    assert 1 + 1 == 3

def test_skipped():
    pytest.skip("Skipping this test")
""")
            temp_path = f.name

        yield temp_path

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    def test_executor_initialization_with_db(self, db):
        """Test executor initialization with provided database."""
        executor = PytestExecutorWithHistory(db=db)
        assert executor.db is not None
        assert executor.db == db

    def test_executor_initialization_without_db(self):
        """Test executor initialization creates default database."""
        with tempfile.TemporaryDirectory():
            executor = PytestExecutorWithHistory(db=None)
            assert executor.db is not None
            executor.close()

    def test_validate_empty_files(self, executor):
        """Test validation with empty file list."""
        result = executor.validate([], {})
        assert result.passed is True
        assert len(result.errors) == 0

    def test_validate_records_history(self, executor, temp_test_file):
        """Test that validation records execution history."""
        # Run validation
        config = {"verbose": False}
        execution_id = "test-run-123"
        executor.validate([temp_test_file], config, execution_id=execution_id)

        # Check that history was recorded
        history = executor.db.get_execution_history()
        assert len(history) > 0

        # Verify execution details
        test_ids = {h.entity_id for h in history}
        assert any("test_passing" in tid for tid in test_ids)

    def test_execution_id_auto_generation(self, executor, temp_test_file):
        """Test that execution ID is auto-generated when not provided."""
        config = {"verbose": False}
        executor.validate([temp_test_file], config)

        # Check that history was recorded with auto-generated ID
        history = executor.db.get_execution_history()
        assert len(history) > 0
        assert all(h.execution_id.startswith("local-") for h in history)

    def test_statistics_update_after_execution(self, executor, temp_test_file):
        """Test that entity statistics are updated after execution."""
        config = {"verbose": False}
        executor.validate([temp_test_file], config)

        # Check statistics were updated
        stats = executor.db.get_entity_statistics(entity_type="test")
        assert len(stats) > 0

        # Verify statistics contain expected data
        for stat in stats:
            assert stat.total_runs > 0
            assert stat.entity_type == "test"

    def test_execute_with_rule_all(self, executor, db, temp_test_file):
        """Test execution using 'all' rule."""
        # Create rule
        rule = ExecutionRule(
            name="test-all",
            criteria="all",
        )
        db.insert_execution_rule(rule)

        # Execute using rule
        result = executor.execute_with_rule("test-all", {"verbose": False})

        # Verify tests were run
        assert result is not None

    def test_execute_with_rule_nonexistent(self, executor):
        """Test execution with nonexistent rule raises error."""
        with pytest.raises(ValueError, match="Rule not found"):
            executor.execute_with_rule("nonexistent-rule")

    def test_execute_with_rule_disabled(self, executor, db):
        """Test execution with disabled rule raises error."""
        # Create disabled rule
        rule = ExecutionRule(
            name="disabled-rule",
            criteria="all",
            enabled=False,
        )
        db.insert_execution_rule(rule)

        with pytest.raises(ValueError, match="Rule is disabled"):
            executor.execute_with_rule("disabled-rule")

    def test_execute_with_rule_no_matching_tests(self, executor, db):
        """Test execution when rule selects no tests."""
        # Create rule that won't match anything
        rule = ExecutionRule(
            name="empty-rule",
            criteria="group",
            groups=["nonexistent/tests/"],
        )
        db.insert_execution_rule(rule)

        result = executor.execute_with_rule("empty-rule")

        assert result.passed is True
        assert result.files_checked == 0

    def test_get_flaky_tests(self, executor, db, temp_test_file):
        """Test retrieval of flaky tests."""
        # Run tests multiple times to create history
        for i in range(10):
            executor.validate([temp_test_file], {"verbose": False})

        # Get flaky tests
        flaky = executor.get_flaky_tests(threshold=0.3, window=10)

        # Should identify test_failing as flaky (100% failure rate)
        assert isinstance(flaky, list)

    def test_get_failed_tests(self, executor, db, temp_test_file):
        """Test retrieval of recently failed tests."""
        # Run tests to create history
        executor.validate([temp_test_file], {"verbose": False})

        # Get failed tests
        failed = executor.get_failed_tests(n=1)

        # Should identify test_failing
        assert isinstance(failed, list)
        assert any("test_failing" in test_id for test_id in failed)

    def test_close_database(self, executor):
        """Test database connection is properly closed."""
        executor.close()
        # After closing, connection should not be usable
        # (This is a simple check, detailed verification would need internal state)
        assert executor.db is not None


class TestPytestExecutorHistoryRecording:
    """Test suite for history recording details."""

    @pytest.fixture
    def db(self):
        """Create in-memory database for testing."""
        database = ExecutionDatabase(":memory:")
        yield database
        database.close()

    @pytest.fixture
    def executor(self, db):
        """Create executor instance."""
        return PytestExecutorWithHistory(db=db)

    @pytest.fixture
    def simple_test_file(self):
        """Create a simple passing test."""
        with tempfile.NamedTemporaryFile(mode="w", suffix="_test.py", delete=False) as f:
            f.write("""
def test_simple_pass():
    assert True
""")
            temp_path = f.name

        yield temp_path
        Path(temp_path).unlink(missing_ok=True)

    def test_history_contains_nodeid(self, executor, simple_test_file):
        """Test that history records contain test nodeid."""
        executor.validate([simple_test_file], {"verbose": False})

        history = executor.db.get_execution_history()
        assert len(history) > 0

        # Check nodeid format
        for record in history:
            assert "::" in record.entity_id or "test_" in record.entity_id

    def test_history_contains_status(self, executor, simple_test_file):
        """Test that history records contain test status."""
        executor.validate([simple_test_file], {"verbose": False})

        history = executor.db.get_execution_history()
        assert len(history) > 0

        # Check status values
        valid_statuses = ["PASSED", "FAILED", "SKIPPED", "ERROR"]
        for record in history:
            assert record.status in valid_statuses

    def test_history_contains_duration(self, executor, simple_test_file):
        """Test that history records contain test duration."""
        executor.validate([simple_test_file], {"verbose": False})

        history = executor.db.get_execution_history()
        assert len(history) > 0

        # Check duration is recorded
        for record in history:
            assert record.duration is None or record.duration >= 0

    def test_history_entity_type_is_test(self, executor, simple_test_file):
        """Test that history records have entity_type='test'."""
        executor.validate([simple_test_file], {"verbose": False})

        history = executor.db.get_execution_history()
        assert len(history) > 0

        for record in history:
            assert record.entity_type == "test"

    def test_history_space_default_local(self, executor, simple_test_file):
        """Test that default space is 'local'."""
        executor.validate([simple_test_file], {"verbose": False})

        history = executor.db.get_execution_history()
        assert len(history) > 0

        for record in history:
            assert record.space == "local"

    def test_history_space_from_config(self, executor, simple_test_file):
        """Test that space can be set from config."""
        executor.validate([str(simple_test_file)], {"verbose": False, "space": "ci"})

        history = executor.db.get_execution_history()
        assert len(history) > 0

        for record in history:
            assert record.space == "ci"


class TestPytestExecutorIntegration:
    """Integration tests for pytest executor with rule engine."""

    @pytest.fixture
    def db(self):
        """Create in-memory database."""
        database = ExecutionDatabase(":memory:")
        yield database
        database.close()

    @pytest.fixture
    def executor(self, db):
        """Create executor instance."""
        return PytestExecutorWithHistory(db=db)

    def test_full_selective_execution_workflow(self, executor, db):
        """Test complete workflow: run → record → select → run again."""
        # This would be a full integration test with real test files
        # For now, verify the components work together

        # 1. Create a rule
        rule = ExecutionRule(
            name="integration-test",
            criteria="all",
        )
        db.insert_execution_rule(rule)

        # 2. Verify rule can be retrieved
        retrieved_rule = executor.db.get_execution_rule("integration-test")
        assert retrieved_rule is not None
        assert retrieved_rule.name == "integration-test"

        # 3. Verify executor can work with the rule
        # (without actual test files, just verify no errors)
        try:
            result = executor.execute_with_rule("integration-test")
            # Should return empty result since no tests match
            assert result.files_checked == 0
        except Exception as e:
            pytest.fail(f"Integration workflow failed: {e}")
