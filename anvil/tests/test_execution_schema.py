"""
Tests for execution schema and database operations.

Following TDD principles: Tests written before full implementation.
"""

import json
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from anvil.storage.execution_schema import (
    EntityStatistics,
    ExecutionDatabase,
    ExecutionHistory,
    ExecutionRule,
)


class TestExecutionDatabase:
    """Test suite for ExecutionDatabase."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db = ExecutionDatabase(db_path)
        yield db
        db.close()
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def memory_db(self):
        """Create an in-memory database for testing."""
        db = ExecutionDatabase(":memory:")
        yield db
        db.close()

    def test_database_initialization(self, temp_db):
        """Test that database initializes with correct schema."""
        # Verify tables exist
        cursor = temp_db.connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        assert "execution_history" in tables
        assert "execution_rules" in tables
        assert "entity_statistics" in tables

    def test_execution_history_insert(self, memory_db):
        """Test insertion of execution history records."""
        record = ExecutionHistory(
            execution_id="local-123",
            entity_id="tests/test_example.py::test_func",
            entity_type="test",
            timestamp=datetime(2026, 2, 1, 10, 0, 0),
            status="PASSED",
            duration=1.23,
            space="local",
            metadata={"platform": "linux"},
        )

        record_id = memory_db.insert_execution_history(record)
        assert record_id > 0

    def test_execution_history_retrieval(self, memory_db):
        """Test retrieval of execution history records."""
        # Insert multiple records
        now = datetime.now()
        records = [
            ExecutionHistory(
                execution_id="local-1",
                entity_id="tests/test_a.py::test_1",
                entity_type="test",
                timestamp=now - timedelta(hours=2),
                status="PASSED",
                duration=1.0,
            ),
            ExecutionHistory(
                execution_id="local-2",
                entity_id="tests/test_a.py::test_1",
                entity_type="test",
                timestamp=now - timedelta(hours=1),
                status="FAILED",
                duration=2.0,
            ),
            ExecutionHistory(
                execution_id="local-3",
                entity_id="tests/test_b.py::test_2",
                entity_type="test",
                timestamp=now,
                status="PASSED",
                duration=0.5,
            ),
        ]

        for record in records:
            memory_db.insert_execution_history(record)

        # Retrieve all records
        all_records = memory_db.get_execution_history()
        assert len(all_records) == 3

        # Retrieve by entity_id
        test_a_records = memory_db.get_execution_history(
            entity_id="tests/test_a.py::test_1"
        )
        assert len(test_a_records) == 2

        # Retrieve by entity_type
        test_records = memory_db.get_execution_history(entity_type="test")
        assert len(test_records) == 3

        # Retrieve with limit
        limited = memory_db.get_execution_history(limit=2)
        assert len(limited) == 2

    def test_execution_history_ordering(self, memory_db):
        """Test that execution history is ordered by timestamp descending."""
        now = datetime.now()
        records = [
            ExecutionHistory(
                execution_id="local-1",
                entity_id="tests/test.py::test_1",
                entity_type="test",
                timestamp=now - timedelta(hours=3),
                status="PASSED",
                duration=1.0,
            ),
            ExecutionHistory(
                execution_id="local-2",
                entity_id="tests/test.py::test_1",
                entity_type="test",
                timestamp=now,
                status="FAILED",
                duration=2.0,
            ),
        ]

        for record in records:
            memory_db.insert_execution_history(record)

        retrieved = memory_db.get_execution_history()
        # Most recent first
        assert retrieved[0].execution_id == "local-2"
        assert retrieved[1].execution_id == "local-1"

    def test_execution_rule_insert(self, memory_db):
        """Test insertion of execution rules."""
        rule = ExecutionRule(
            name="quick-check",
            criteria="group",
            enabled=True,
            threshold=None,
            window=None,
            groups=["tests/test_models.py", "tests/test_parser.py"],
            executor_config={"verbose": True},
        )

        rule_id = memory_db.insert_execution_rule(rule)
        assert rule_id > 0

    def test_execution_rule_retrieval(self, memory_db):
        """Test retrieval of execution rules."""
        rule = ExecutionRule(
            name="flaky-tests",
            criteria="failure-rate",
            enabled=True,
            threshold=0.10,
            window=20,
            groups=None,
            executor_config=None,
        )

        memory_db.insert_execution_rule(rule)

        retrieved = memory_db.get_execution_rule("flaky-tests")
        assert retrieved is not None
        assert retrieved.name == "flaky-tests"
        assert retrieved.criteria == "failure-rate"
        assert retrieved.threshold == 0.10
        assert retrieved.window == 20
        assert retrieved.enabled is True

    def test_execution_rule_not_found(self, memory_db):
        """Test retrieval of non-existent rule."""
        rule = memory_db.get_execution_rule("nonexistent")
        assert rule is None

    def test_entity_statistics_upsert(self, memory_db):
        """Test upsert of entity statistics."""
        stats = EntityStatistics(
            entity_id="tests/test_example.py::test_func",
            entity_type="test",
            total_runs=10,
            passed=8,
            failed=2,
            skipped=0,
            failure_rate=0.2,
            avg_duration=1.5,
            last_run=datetime.now(),
            last_failure=datetime.now() - timedelta(hours=1),
        )

        # Insert
        stats_id = memory_db.update_entity_statistics(stats)
        assert stats_id > 0

        # Update
        stats.total_runs = 15
        stats.passed = 12
        stats.failed = 3
        stats.failure_rate = 0.2

        updated_id = memory_db.update_entity_statistics(stats)
        # Should be same ID (upsert)
        assert updated_id == stats_id

    def test_entity_statistics_retrieval(self, memory_db):
        """Test retrieval of entity statistics."""
        # Insert multiple statistics
        stats_list = [
            EntityStatistics(
                entity_id="tests/test_a.py::test_1",
                entity_type="test",
                total_runs=10,
                passed=10,
                failed=0,
                failure_rate=0.0,
                avg_duration=1.0,
            ),
            EntityStatistics(
                entity_id="tests/test_b.py::test_2",
                entity_type="test",
                total_runs=20,
                passed=15,
                failed=5,
                failure_rate=0.25,
                avg_duration=2.0,
            ),
        ]

        for stats in stats_list:
            memory_db.update_entity_statistics(stats)

        # Retrieve all
        all_stats = memory_db.get_entity_statistics()
        assert len(all_stats) == 2

        # Retrieve by entity_id
        test_a_stats = memory_db.get_entity_statistics(
            entity_id="tests/test_a.py::test_1"
        )
        assert len(test_a_stats) == 1
        assert test_a_stats[0].failure_rate == 0.0

        # Retrieve by entity_type
        test_stats = memory_db.get_entity_statistics(entity_type="test")
        assert len(test_stats) == 2

    def test_execution_history_metadata_serialization(self, memory_db):
        """Test that metadata is correctly serialized/deserialized."""
        metadata = {
            "platform": "linux",
            "python_version": "3.11",
            "tags": ["slow", "integration"],
        }

        record = ExecutionHistory(
            execution_id="local-123",
            entity_id="tests/test_example.py::test_func",
            entity_type="test",
            timestamp=datetime.now(),
            status="PASSED",
            duration=1.23,
            metadata=metadata,
        )

        memory_db.insert_execution_history(record)

        retrieved = memory_db.get_execution_history(
            entity_id="tests/test_example.py::test_func"
        )
        assert len(retrieved) == 1
        assert retrieved[0].metadata == metadata

    def test_execution_rule_groups_serialization(self, memory_db):
        """Test that groups are correctly serialized/deserialized."""
        groups = [
            "tests/test_models.py",
            "tests/test_parser.py",
            "tests/test_executor.py",
        ]

        rule = ExecutionRule(
            name="quick-check",
            criteria="group",
            groups=groups,
        )

        memory_db.insert_execution_rule(rule)

        retrieved = memory_db.get_execution_rule("quick-check")
        assert retrieved.groups == groups

    def test_database_auto_recovery(self):
        """Test database auto-recovery from corruption."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        # Create a corrupted database file
        with open(db_path, "w") as f:
            f.write("corrupted data")

        # Should recover automatically
        db = ExecutionDatabase(db_path, auto_recover=True)

        # Should be functional
        cursor = db.connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        assert "execution_history" in tables

        db.close()
        Path(db_path).unlink(missing_ok=True)

    def test_database_corruption_without_recovery(self):
        """Test database corruption raises error without auto_recover."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Create a corrupted database file
            with open(db_path, "w") as f:
                f.write("corrupted data")

            # Should raise error
            with pytest.raises(sqlite3.DatabaseError):
                db = ExecutionDatabase(db_path, auto_recover=False)
                db.close()  # Ensure connection is closed if created
        finally:
            # Clean up on Windows - add delay for file lock release
            import time

            time.sleep(0.2)
            try:
                Path(db_path).unlink()
            except PermissionError:
                # If still locked, just skip - temp dir will clean up eventually
                pass

    def test_foreign_keys_enabled(self, memory_db):
        """Test that foreign keys are enabled."""
        cursor = memory_db.connection.cursor()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        assert result[0] == 1  # Foreign keys enabled


class TestExecutionHistoryDataclass:
    """Test ExecutionHistory dataclass."""

    def test_execution_history_creation(self):
        """Test creation of ExecutionHistory record."""
        timestamp = datetime(2026, 2, 1, 10, 0, 0)
        record = ExecutionHistory(
            execution_id="local-123",
            entity_id="tests/test_example.py::test_func",
            entity_type="test",
            timestamp=timestamp,
            status="PASSED",
            duration=1.23,
            space="local",
            metadata={"platform": "linux"},
        )

        assert record.execution_id == "local-123"
        assert record.entity_id == "tests/test_example.py::test_func"
        assert record.entity_type == "test"
        assert record.timestamp == timestamp
        assert record.status == "PASSED"
        assert record.duration == 1.23
        assert record.space == "local"
        assert record.metadata == {"platform": "linux"}
        assert record.id is None

    def test_execution_history_defaults(self):
        """Test default values for ExecutionHistory."""
        record = ExecutionHistory(
            execution_id="local-123",
            entity_id="tests/test_example.py::test_func",
            entity_type="test",
            timestamp=datetime.now(),
            status="PASSED",
            duration=None,
        )

        assert record.space == "local"
        assert record.metadata is None
        assert record.id is None


class TestExecutionRuleDataclass:
    """Test ExecutionRule dataclass."""

    def test_execution_rule_creation(self):
        """Test creation of ExecutionRule."""
        rule = ExecutionRule(
            name="quick-check",
            criteria="group",
            enabled=True,
            threshold=None,
            window=None,
            groups=["tests/test_models.py"],
            executor_config={"verbose": True},
        )

        assert rule.name == "quick-check"
        assert rule.criteria == "group"
        assert rule.enabled is True
        assert rule.groups == ["tests/test_models.py"]
        assert rule.executor_config == {"verbose": True}

    def test_execution_rule_defaults(self):
        """Test default values for ExecutionRule."""
        rule = ExecutionRule(
            name="baseline-all",
            criteria="all",
        )

        assert rule.enabled is True
        assert rule.threshold is None
        assert rule.window is None
        assert rule.groups is None
        assert rule.executor_config is None


class TestEntityStatisticsDataclass:
    """Test EntityStatistics dataclass."""

    def test_entity_statistics_creation(self):
        """Test creation of EntityStatistics."""
        now = datetime.now()
        stats = EntityStatistics(
            entity_id="tests/test_example.py::test_func",
            entity_type="test",
            total_runs=10,
            passed=8,
            failed=2,
            skipped=0,
            failure_rate=0.2,
            avg_duration=1.5,
            last_run=now,
            last_failure=now - timedelta(hours=1),
        )

        assert stats.entity_id == "tests/test_example.py::test_func"
        assert stats.entity_type == "test"
        assert stats.total_runs == 10
        assert stats.passed == 8
        assert stats.failed == 2
        assert stats.failure_rate == 0.2
        assert stats.avg_duration == 1.5

    def test_entity_statistics_defaults(self):
        """Test default values for EntityStatistics."""
        stats = EntityStatistics(
            entity_id="tests/test_example.py::test_func",
            entity_type="test",
        )

        assert stats.total_runs == 0
        assert stats.passed == 0
        assert stats.failed == 0
        assert stats.skipped == 0
        assert stats.failure_rate == 0.0
        assert stats.avg_duration is None
        assert stats.last_run is None
        assert stats.last_failure is None
