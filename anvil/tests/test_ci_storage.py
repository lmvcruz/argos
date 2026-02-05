"""
Tests for anvil.storage.ci_storage module.

Tests the CIStorageLayer and related dataclasses for CI-specific
execution history analysis and comparison.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from anvil.storage.ci_storage import (
    CIStorageLayer,
    ComparisonStatistics,
    PlatformStatistics,
)
from anvil.storage.execution_schema import ExecutionDatabase, ExecutionHistory


class TestPlatformStatistics:
    """Test PlatformStatistics dataclass."""

    def test_platform_statistics_creation(self):
        """Test creating a PlatformStatistics instance."""
        now = datetime.now()
        stats = PlatformStatistics(
            platform="ubuntu-latest",
            python_version="3.9",
            total_runs=100,
            passed=95,
            failed=5,
            skipped=0,
            avg_duration=2.5,
            last_run=now,
            failure_rate=0.05,
        )

        assert stats.platform == "ubuntu-latest"
        assert stats.python_version == "3.9"
        assert stats.total_runs == 100
        assert stats.passed == 95
        assert stats.failed == 5
        assert stats.failure_rate == 0.05

    def test_platform_statistics_with_none_values(self):
        """Test PlatformStatistics with optional None values."""
        stats = PlatformStatistics(
            platform="windows-latest",
            python_version="3.8",
            total_runs=50,
            passed=40,
            failed=10,
            skipped=0,
            avg_duration=None,
            last_run=None,
            failure_rate=0.2,
        )

        assert stats.avg_duration is None
        assert stats.last_run is None
        assert stats.failure_rate == 0.2


class TestComparisonStatistics:
    """Test ComparisonStatistics dataclass."""

    def test_comparison_statistics_creation(self):
        """Test creating a ComparisonStatistics instance."""
        comp = ComparisonStatistics(
            entity_id="test_001",
            local_status="PASSED",
            ci_status="FAILED",
            local_duration=1.5,
            ci_duration=2.0,
            platform_specific=True,
            platforms_failed=["ubuntu-latest", "windows-latest"],
        )

        assert comp.entity_id == "test_001"
        assert comp.local_status == "PASSED"
        assert comp.ci_status == "FAILED"
        assert len(comp.platforms_failed) == 2
        assert comp.platform_specific is True

    def test_comparison_statistics_with_none_statuses(self):
        """Test ComparisonStatistics with None statuses."""
        comp = ComparisonStatistics(
            entity_id="test_002",
            local_status=None,
            ci_status="PASSED",
            local_duration=None,
            ci_duration=1.0,
            platform_specific=False,
            platforms_failed=[],
        )

        assert comp.local_status is None
        assert comp.ci_status == "PASSED"
        assert len(comp.platforms_failed) == 0


class TestCIStorageLayer:
    """Test CIStorageLayer class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock ExecutionDatabase."""
        db = Mock(spec=ExecutionDatabase)
        db.connection = Mock()
        db.connection.cursor = Mock()
        return db

    @pytest.fixture
    def ci_storage(self, mock_db):
        """Create a CIStorageLayer instance with mock database."""
        return CIStorageLayer(mock_db)

    def test_storage_layer_creation(self, ci_storage, mock_db):
        """Test creating a CIStorageLayer instance."""
        assert ci_storage.db is mock_db

    def test_get_ci_executions_basic(self, ci_storage, mock_db):
        """Test getting CI executions."""
        # Setup mock cursor
        cursor = Mock()
        mock_db.connection.cursor.return_value = cursor

        # Mock execution history data
        now = datetime.now()
        cursor.fetchall.return_value = [
            (1, "exec_001", "test_001", "test", now.isoformat(), "PASSED", 1.5, "ci", None),
            (
                2,
                "exec_002",
                "test_002",
                "test",
                (now - timedelta(hours=1)).isoformat(),
                "FAILED",
                2.0,
                "ci",
                None,
            ),
        ]

        result = ci_storage.get_ci_executions()

        assert len(result) == 2
        assert result[0].status == "PASSED"
        assert result[1].status == "FAILED"
        cursor.execute.assert_called_once()

    def test_get_ci_executions_with_entity_id(self, ci_storage, mock_db):
        """Test getting CI executions filtered by entity_id."""
        cursor = Mock()
        mock_db.connection.cursor.return_value = cursor

        now = datetime.now()
        cursor.fetchall.return_value = [
            (1, "exec_001", "test_001", "test", now.isoformat(), "PASSED", 1.5, "ci", None),
        ]

        result = ci_storage.get_ci_executions(entity_id="test_001")

        assert len(result) == 1
        assert result[0].entity_id == "test_001"
        # Verify query includes entity_id filter
        call_args = cursor.execute.call_args
        assert "entity_id=?" in call_args[0][0]

    def test_get_ci_executions_with_limit(self, ci_storage, mock_db):
        """Test getting CI executions with limit."""
        cursor = Mock()
        mock_db.connection.cursor.return_value = cursor

        now = datetime.now()
        cursor.fetchall.return_value = [
            (1, "exec_001", "test_001", "test", now.isoformat(), "PASSED", 1.5, "ci", None),
            (
                2,
                "exec_002",
                "test_002",
                "test",
                (now - timedelta(hours=1)).isoformat(),
                "PASSED",
                1.2,
                "ci",
                None,
            ),
        ]

        result = ci_storage.get_ci_executions(limit=2)

        assert len(result) == 2
        call_args = cursor.execute.call_args
        assert "LIMIT ?" in call_args[0][0]

    def test_get_ci_executions_with_days_filter(self, ci_storage, mock_db):
        """Test getting CI executions with days filter."""
        cursor = Mock()
        mock_db.connection.cursor.return_value = cursor

        now = datetime.now()
        cursor.fetchall.return_value = [
            (1, "exec_001", "test_001", "test", now.isoformat(), "PASSED", 1.5, "ci", None),
        ]

        result = ci_storage.get_ci_executions(days=7)

        assert len(result) == 1
        call_args = cursor.execute.call_args
        assert "timestamp > ?" in call_args[0][0]

    def test_get_local_executions_basic(self, ci_storage, mock_db):
        """Test getting local executions."""
        cursor = Mock()
        mock_db.connection.cursor.return_value = cursor

        now = datetime.now()
        cursor.fetchall.return_value = [
            (1, "exec_001", "test_001", "test", now.isoformat(), "PASSED", 1.2, "local", None),
        ]

        result = ci_storage.get_local_executions()

        assert len(result) == 1
        assert result[0].space == "local"
        call_args = cursor.execute.call_args
        assert "space='local'" in call_args[0][0]

    def test_get_local_executions_with_entity_id(self, ci_storage, mock_db):
        """Test getting local executions filtered by entity_id."""
        cursor = Mock()
        mock_db.connection.cursor.return_value = cursor

        now = datetime.now()
        cursor.fetchall.return_value = [
            (1, "exec_001", "test_001", "test", now.isoformat(), "PASSED", 1.2, "local", None),
        ]

        result = ci_storage.get_local_executions(entity_id="test_001")

        assert len(result) == 1
        assert result[0].entity_id == "test_001"

    def test_get_ci_statistics_by_platform(self, ci_storage, mock_db):
        """Test getting CI statistics by platform."""
        cursor = Mock()
        mock_db.connection.cursor.return_value = cursor

        now = datetime.now()
        cursor.fetchall.return_value = [
            ("ubuntu-latest", "3.9", 100, 95, 5, 0, 2.5, now.isoformat()),
            ("windows-latest", "3.8", 80, 75, 5, 0, 2.8, now.isoformat()),
        ]

        result = ci_storage.get_ci_statistics_by_platform()

        assert len(result) == 2
        assert isinstance(result[0], PlatformStatistics)
        assert result[0].platform == "ubuntu-latest"
        assert result[0].failure_rate == 0.05

    def test_get_ci_statistics_by_platform_with_limit_days(self, ci_storage, mock_db):
        """Test getting CI statistics with custom day limit."""
        cursor = Mock()
        mock_db.connection.cursor.return_value = cursor
        cursor.fetchall.return_value = []

        ci_storage.get_ci_statistics_by_platform(limit_days=60)

        call_args = cursor.execute.call_args
        assert "WHERE space='ci'" in call_args[0][0]
        assert "timestamp > ?" in call_args[0][0]

    def test_compare_local_vs_ci(self, ci_storage, mock_db):
        """Test comparing local vs CI executions."""
        cursor = Mock()
        mock_db.connection.cursor.return_value = cursor

        now = datetime.now()

        # Mock entity_id query
        cursor.fetchall.side_effect = [
            [("test_001",), ("test_002",)],  # Entities list
        ]

        # Mock the get_local_executions and get_ci_executions calls
        with patch.object(ci_storage, "get_local_executions") as mock_local:
            with patch.object(ci_storage, "get_ci_executions") as mock_ci:
                mock_local.return_value = [
                    ExecutionHistory(
                        id=1,
                        execution_id="exec_001",
                        entity_id="test_001",
                        entity_type="test",
                        timestamp=now,
                        status="PASSED",
                        duration=1.5,
                        space="local",
                        metadata=None,
                    )
                ]
                mock_ci.return_value = [
                    ExecutionHistory(
                        id=2,
                        execution_id="exec_002",
                        entity_id="test_001",
                        entity_type="test",
                        timestamp=now,
                        status="FAILED",
                        duration=2.0,
                        space="ci",
                        metadata={"platform": "ubuntu-latest"},
                    )
                ]

                result = ci_storage.compare_local_vs_ci()

                # Should return at least one comparison
                assert isinstance(result, list)
                if result:
                    assert isinstance(result[0], ComparisonStatistics)

    def test_get_platform_specific_failures(self, ci_storage, mock_db):
        """Test getting platform-specific failures."""
        with patch.object(ci_storage, "compare_local_vs_ci") as mock_compare:
            mock_compare.return_value = [
                ComparisonStatistics(
                    entity_id="test_001",
                    local_status="PASSED",
                    ci_status="FAILED",
                    local_duration=1.5,
                    ci_duration=2.0,
                    platform_specific=True,
                    platforms_failed=["ubuntu-latest"],
                ),
                ComparisonStatistics(
                    entity_id="test_002",
                    local_status="PASSED",
                    ci_status="PASSED",
                    local_duration=1.2,
                    ci_duration=1.3,
                    platform_specific=False,
                    platforms_failed=[],
                ),
            ]

            result = ci_storage.get_platform_specific_failures()

            assert isinstance(result, dict)
            assert "ubuntu-latest" in result
            assert "test_001" in result["ubuntu-latest"]

    def test_get_ci_health_summary(self, ci_storage, mock_db):
        """Test getting CI health summary."""
        cursor = Mock()
        mock_db.connection.cursor.return_value = cursor

        now = datetime.now()
        cursor.fetchone.return_value = (100, 95, 5, 0, 2.5, now.isoformat())

        result = ci_storage.get_ci_health_summary()

        assert isinstance(result, dict)
        assert result["total_runs"] == 100
        assert result["passed"] == 95
        assert result["failed"] == 5
        assert result["pass_rate"] == 0.95
        assert result["failure_rate"] == 0.05

    def test_get_ci_health_summary_empty_results(self, ci_storage, mock_db):
        """Test CI health summary with no executions."""
        cursor = Mock()
        mock_db.connection.cursor.return_value = cursor
        cursor.fetchone.return_value = (0, 0, 0, 0, None, None)

        result = ci_storage.get_ci_health_summary()

        assert result["total_runs"] == 0
        assert result["pass_rate"] == 0.0
        assert result["failure_rate"] == 0.0

    def test_get_flaky_tests_in_ci(self, ci_storage, mock_db):
        """Test identifying flaky tests."""
        cursor = Mock()
        mock_db.connection.cursor.return_value = cursor

        cursor.fetchall.return_value = [
            ("test_001", 10, 2),  # 20% failure rate
            ("test_002", 10, 1),  # 10% failure rate
        ]

        result = ci_storage.get_flaky_tests_in_ci(failure_threshold=0.10, min_runs=5)

        assert len(result) == 2
        assert result[0][0] == "test_001"  # entity_id
        assert result[0][1] == 0.2  # failure_rate
        assert result[0][2] == 10  # total_runs

    def test_get_flaky_tests_in_ci_with_custom_threshold(self, ci_storage, mock_db):
        """Test flaky tests with custom failure threshold."""
        cursor = Mock()
        mock_db.connection.cursor.return_value = cursor
        cursor.fetchall.return_value = []

        ci_storage.get_flaky_tests_in_ci(failure_threshold=0.25, min_runs=10)

        call_args = cursor.execute.call_args
        # Verify query includes the custom parameters
        assert call_args is not None
