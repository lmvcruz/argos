"""
Tests for Scout-Anvil integration module.

Tests the bridge between Scout's CI data storage and Anvil's
validation history database.
"""

import sys
from unittest.mock import Mock, patch

import pytest

from scout.integration import AnvilBridge


class TestIntegrationModuleImports:
    """Test integration module imports."""

    def test_anvil_bridge_import(self):
        """Test that AnvilBridge can be imported from integration module."""
        from scout.integration import AnvilBridge

        assert AnvilBridge is not None
        assert callable(AnvilBridge)


class TestAnvilBridge:
    """Test AnvilBridge class."""

    def test_init_without_anvil_raises_import_error(self):
        """Test initialization fails gracefully when Anvil is not installed."""
        # Save original sys.modules entry
        original_modules = sys.modules.copy()
        import builtins

        original_import = builtins.__import__

        try:
            # Remove anvil module if it exists
            if "anvil.storage.statistics_database" in sys.modules:
                del sys.modules["anvil.storage.statistics_database"]

            # Mock the import to fail
            def mock_import(name, *args, **kwargs):
                if "anvil" in name:
                    raise ImportError("No module named 'anvil'")
                return original_import(name, *args, **kwargs)

            builtins.__import__ = mock_import

            with patch("scout.integration.anvil_bridge.DatabaseManager"):
                with pytest.raises(ImportError):
                    AnvilBridge("scout.db", "anvil.db")
        finally:
            # Restore original import and modules
            builtins.__import__ = original_import
            sys.modules.update(original_modules)

    @patch("scout.integration.anvil_bridge.DatabaseManager")
    def test_init_with_anvil_success(self, mock_db_manager):
        """Test successful initialization when Anvil is available."""
        # Mock Anvil StatisticsDatabase
        mock_stats_db_class = Mock()
        mock_stats_db_instance = Mock()
        mock_stats_db_class.return_value = mock_stats_db_instance

        # Create mock module
        mock_anvil_module = Mock()
        mock_anvil_module.StatisticsDatabase = mock_stats_db_class

        with patch.dict("sys.modules", {"anvil.storage.statistics_database": mock_anvil_module}):
            bridge = AnvilBridge("scout.db", "anvil.db")

            assert bridge.scout_db is not None
            assert bridge.anvil_db == mock_stats_db_instance
            mock_db_manager.assert_called_once_with("scout.db")
            mock_db_manager.return_value.initialize.assert_called_once()

    @patch("scout.integration.anvil_bridge.DatabaseManager")
    def test_sync_ci_run_to_anvil_run_not_found(self, mock_db_manager):
        """Test sync_ci_run_to_anvil raises ValueError when run not found."""
        # Mock database setup
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_db_manager.return_value.get_session.return_value = mock_session

        # Mock Anvil
        mock_stats_db_class = Mock()
        mock_anvil_module = Mock()
        mock_anvil_module.StatisticsDatabase = mock_stats_db_class

        with patch.dict("sys.modules", {"anvil.storage.statistics_database": mock_anvil_module}):
            bridge = AnvilBridge("scout.db", "anvil.db")

            with pytest.raises(ValueError, match="Workflow run 999 not found"):
                bridge.sync_ci_run_to_anvil(999)

    @patch("scout.integration.anvil_bridge.DatabaseManager")
    def test_sync_ci_run_to_anvil_success(self, mock_db_manager):
        """Test successful sync of CI run to Anvil."""
        from datetime import datetime

        # Mock workflow run
        mock_run = Mock()
        mock_run.run_id = 123
        mock_run.workflow_name = "Test Workflow"
        mock_run.started_at = datetime(2026, 2, 1, 10, 0)
        mock_run.commit_sha = "abc123"
        mock_run.branch = "main"
        mock_run.conclusion = "success"
        mock_run.duration_seconds = 300

        # Mock jobs and test results
        mock_job = Mock()
        mock_job.job_id = 456
        mock_job.job_name = "test (ubuntu, 3.10)"
        mock_job.runner_os = "ubuntu-latest"

        mock_test_result = Mock()
        mock_test_result.test_nodeid = "tests/test_file.py::TestClass::test_method"
        mock_test_result.outcome = "passed"
        mock_test_result.duration = 1.5
        mock_test_result.error_message = None

        # Mock session
        mock_session = Mock()

        # Mock query for workflow run
        from scout.storage.schema import WorkflowJob, WorkflowRun, WorkflowTestResult

        def query_side_effect(model):
            if model == WorkflowRun:
                result = Mock()
                result.filter_by.return_value.first.return_value = mock_run
                return result
            elif model == WorkflowJob:
                result = Mock()
                result.filter_by.return_value.all.return_value = [mock_job]
                return result
            elif model == WorkflowTestResult:
                result = Mock()
                result.filter_by.return_value.all.return_value = [mock_test_result]
                return result
            return Mock()

        mock_session.query = Mock(side_effect=query_side_effect)
        mock_db_manager.return_value.get_session.return_value = mock_session

        # Mock Anvil database
        mock_stats_db_instance = Mock()
        mock_stats_db_instance.insert_validation_run.return_value = 789
        mock_stats_db_class = Mock(return_value=mock_stats_db_instance)

        # Mock ValidationRun and TestCaseRecord
        mock_validation_run = Mock()
        mock_test_case_record = Mock()

        mock_anvil_module = Mock()
        mock_anvil_module.StatisticsDatabase = mock_stats_db_class
        mock_anvil_module.ValidationRun = mock_validation_run
        mock_anvil_module.TestCaseRecord = mock_test_case_record

        with patch.dict("sys.modules", {"anvil.storage.statistics_database": mock_anvil_module}):
            bridge = AnvilBridge("scout.db", "anvil.db")

            result = bridge.sync_ci_run_to_anvil(123, verbose=True)

            assert result["validation_run_id"] == 789
            assert result["tests_synced"] == 1
            assert result["jobs_synced"] == 1

    @patch("scout.integration.anvil_bridge.DatabaseManager")
    def test_sync_recent_runs_success(self, mock_db_manager):
        """Test syncing recent runs."""
        from datetime import datetime

        # Mock workflow runs
        mock_run1 = Mock()
        mock_run1.run_id = 123
        mock_run1.workflow_name = "Test1"
        mock_run1.started_at = datetime(2026, 2, 1, 10, 0)

        mock_run2 = Mock()
        mock_run2.run_id = 124
        mock_run2.workflow_name = "Test2"
        mock_run2.started_at = datetime(2026, 2, 1, 9, 0)

        # Mock session
        mock_session = Mock()
        mock_query = Mock()
        mock_query.order_by.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.limit.return_value.all.return_value = [mock_run1, mock_run2]
        mock_session.query.return_value = mock_query

        mock_db_manager.return_value.get_session.return_value = mock_session

        # Mock Anvil
        mock_stats_db_class = Mock()
        mock_anvil_module = Mock()
        mock_anvil_module.StatisticsDatabase = mock_stats_db_class

        with patch.dict("sys.modules", {"anvil.storage.statistics_database": mock_anvil_module}):
            bridge = AnvilBridge("scout.db", "anvil.db")

            # Mock sync_ci_run_to_anvil
            bridge.sync_ci_run_to_anvil = Mock(
                return_value={"validation_run_id": 1, "tests_synced": 5, "jobs_synced": 1}
            )

            results = bridge.sync_recent_runs(limit=2, verbose=True)

            assert len(results) == 2
            assert bridge.sync_ci_run_to_anvil.call_count == 2

    @patch("scout.integration.anvil_bridge.DatabaseManager")
    def test_sync_recent_runs_with_workflow_filter(self, mock_db_manager):
        """Test syncing recent runs with workflow name filter."""
        from datetime import datetime

        # Mock workflow run
        mock_run = Mock()
        mock_run.run_id = 123
        mock_run.workflow_name = "CI Tests"
        mock_run.started_at = datetime(2026, 2, 1, 10, 0)

        # Mock session
        mock_session = Mock()
        mock_query = Mock()
        mock_query.order_by.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.limit.return_value.all.return_value = [mock_run]
        mock_session.query.return_value = mock_query

        mock_db_manager.return_value.get_session.return_value = mock_session

        # Mock Anvil
        mock_stats_db_class = Mock()
        mock_anvil_module = Mock()
        mock_anvil_module.StatisticsDatabase = mock_stats_db_class

        with patch.dict("sys.modules", {"anvil.storage.statistics_database": mock_anvil_module}):
            bridge = AnvilBridge("scout.db", "anvil.db")
            bridge.sync_ci_run_to_anvil = Mock(
                return_value={"validation_run_id": 1, "tests_synced": 3, "jobs_synced": 1}
            )

            results = bridge.sync_recent_runs(limit=10, workflow_name="CI Tests", verbose=False)

            assert len(results) == 1
            # Verify filter_by was called with workflow_name
            mock_query.filter_by.assert_called()

    @patch("scout.integration.anvil_bridge.DatabaseManager")
    def test_sync_recent_runs_handles_errors(self, mock_db_manager):
        """Test that sync_recent_runs handles individual sync errors gracefully."""
        from datetime import datetime

        # Mock workflow runs
        mock_run1 = Mock()
        mock_run1.run_id = 123
        mock_run1.started_at = datetime(2026, 2, 1, 10, 0)

        # Mock session
        mock_session = Mock()
        mock_query = Mock()
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value.all.return_value = [mock_run1]
        mock_session.query.return_value = mock_query

        mock_db_manager.return_value.get_session.return_value = mock_session

        # Mock Anvil
        mock_stats_db_class = Mock()
        mock_anvil_module = Mock()
        mock_anvil_module.StatisticsDatabase = mock_stats_db_class

        with patch.dict("sys.modules", {"anvil.storage.statistics_database": mock_anvil_module}):
            bridge = AnvilBridge("scout.db", "anvil.db")

            # Make sync_ci_run_to_anvil raise an exception
            bridge.sync_ci_run_to_anvil = Mock(side_effect=Exception("Sync failed"))

            results = bridge.sync_recent_runs(limit=1, verbose=True)

            assert len(results) == 1
            assert "error" in results[0]
            assert results[0]["error"] == "Sync failed"
            assert results[0]["run_id"] == 123

    @patch("scout.integration.anvil_bridge.DatabaseManager")
    def test_compare_local_vs_ci(self, mock_db_manager):
        """Test comparing local test results with CI results."""
        # Mock Anvil database with local test results
        mock_anvil_db = Mock()
        mock_local_test1 = Mock()
        mock_local_test1.test_name = "test_feature_a"
        mock_local_test1.passed = True

        mock_local_test2 = Mock()
        mock_local_test2.test_name = "test_feature_b"
        mock_local_test2.passed = False

        mock_local_test3 = Mock()
        mock_local_test3.test_name = "test_only_local"
        mock_local_test3.passed = True

        mock_anvil_db.query_test_cases_for_run.return_value = [
            mock_local_test1,
            mock_local_test2,
            mock_local_test3,
        ]

        # Mock Scout database with CI test results
        mock_ci_test1 = Mock()
        mock_ci_test1.test_nodeid = "tests/test_file.py::TestClass::test_feature_a"
        mock_ci_test1.outcome = "failed"

        mock_ci_test2 = Mock()
        mock_ci_test2.test_nodeid = "tests/test_file.py::TestClass::test_feature_b"
        mock_ci_test2.outcome = "passed"

        mock_ci_test3 = Mock()
        mock_ci_test3.test_nodeid = "tests/test_file.py::test_only_ci"
        mock_ci_test3.outcome = "passed"

        mock_job = Mock()
        mock_job.job_id = 1

        mock_session = Mock()

        from scout.storage.schema import WorkflowJob, WorkflowTestResult

        def query_side_effect(model):
            if model == WorkflowJob:
                result = Mock()
                result.filter_by.return_value.all.return_value = [mock_job]
                return result
            elif model == WorkflowTestResult:
                result = Mock()
                result.filter_by.return_value.all.return_value = [
                    mock_ci_test1,
                    mock_ci_test2,
                    mock_ci_test3,
                ]
                return result
            return Mock()

        mock_session.query = Mock(side_effect=query_side_effect)
        mock_db_manager.return_value.get_session.return_value = mock_session

        # Mock Anvil
        mock_stats_db_class = Mock()
        mock_anvil_module = Mock()
        mock_anvil_module.StatisticsDatabase = mock_stats_db_class

        with patch.dict("sys.modules", {"anvil.storage.statistics_database": mock_anvil_module}):
            bridge = AnvilBridge("scout.db", "anvil.db")
            bridge.anvil_db = mock_anvil_db

            result = bridge.compare_local_vs_ci(anvil_run_id=123, ci_run_id=456)

            # Verify comparisons
            assert "pass_local_fail_ci" in result
            assert "fail_local_pass_ci" in result
            assert "only_local" in result
            assert "only_ci" in result

            assert "test_feature_a" in result["pass_local_fail_ci"]
            assert "test_feature_b" in result["fail_local_pass_ci"]
            assert "test_only_local" in result["only_local"]
            assert "test_only_ci" in result["only_ci"]

            mock_session.close.assert_called_once()

    @patch("scout.integration.anvil_bridge.DatabaseManager")
    def test_identify_ci_specific_failures(self, mock_db_manager):
        """Test finding tests that only fail in CI."""
        from datetime import datetime, timedelta

        # Mock CI test failures
        mock_failure1 = Mock()
        mock_failure1.test_nodeid = "tests/test_file.py::TestClass::test_flaky"
        mock_failure1.outcome = "failed"
        mock_failure1.timestamp = datetime.now()
        mock_failure1.runner_os = "ubuntu-latest"

        mock_failure2 = Mock()
        mock_failure2.test_nodeid = "tests/test_file.py::TestClass::test_flaky"
        mock_failure2.outcome = "failed"
        mock_failure2.timestamp = datetime.now() - timedelta(days=1)
        mock_failure2.runner_os = "windows-latest"

        mock_failure3 = Mock()
        mock_failure3.test_nodeid = "tests/test_file.py::test_another"
        mock_failure3.outcome = "failed"
        mock_failure3.timestamp = datetime.now()
        mock_failure3.runner_os = "macos-latest"

        # Mock session
        mock_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_failure1, mock_failure2, mock_failure3]
        mock_session.query.return_value = mock_query

        mock_db_manager.return_value.get_session.return_value = mock_session

        # Mock Anvil
        mock_stats_db_class = Mock()
        mock_anvil_module = Mock()
        mock_anvil_module.StatisticsDatabase = mock_stats_db_class

        with patch.dict("sys.modules", {"anvil.storage.statistics_database": mock_anvil_module}):
            bridge = AnvilBridge("scout.db", "anvil.db")

            result = bridge.identify_ci_specific_failures(days=7, min_failures=2)

            # Verify results
            assert len(result) == 1
            assert result[0]["test_name"] == "test_flaky"
            assert result[0]["ci_failures"] == 2
            assert set(result[0]["platforms"]) == {"ubuntu-latest", "windows-latest"}

            mock_session.close.assert_called_once()

    @patch("scout.integration.anvil_bridge.DatabaseManager")
    def test_identify_ci_specific_failures_filters_by_min_failures(self, mock_db_manager):
        """Test that identify_ci_specific_failures respects min_failures threshold."""
        from datetime import datetime

        # Mock CI test failures (only 1 failure per test)
        mock_failure = Mock()
        mock_failure.test_nodeid = "tests/test_file.py::test_single_fail"
        mock_failure.outcome = "failed"
        mock_failure.timestamp = datetime.now()
        mock_failure.runner_os = "ubuntu-latest"

        mock_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_failure]
        mock_session.query.return_value = mock_query

        mock_db_manager.return_value.get_session.return_value = mock_session

        # Mock Anvil
        mock_stats_db_class = Mock()
        mock_anvil_module = Mock()
        mock_anvil_module.StatisticsDatabase = mock_stats_db_class

        with patch.dict("sys.modules", {"anvil.storage.statistics_database": mock_anvil_module}):
            bridge = AnvilBridge("scout.db", "anvil.db")

            # Request min_failures=2, so single failure should be filtered out
            result = bridge.identify_ci_specific_failures(days=7, min_failures=2)

            assert len(result) == 0

            mock_session.close.assert_called_once()

    @patch("scout.integration.anvil_bridge.DatabaseManager")
    def test_close_method(self, mock_db_manager):
        """Test the close method."""
        # Mock Anvil with connection
        mock_anvil_db = Mock()
        mock_connection = Mock()
        mock_anvil_db.connection = mock_connection

        mock_stats_db_class = Mock(return_value=mock_anvil_db)
        mock_anvil_module = Mock()
        mock_anvil_module.StatisticsDatabase = mock_stats_db_class

        with patch.dict("sys.modules", {"anvil.storage.statistics_database": mock_anvil_module}):
            bridge = AnvilBridge("scout.db", "anvil.db")

            # Call close
            bridge.close()

            # Verify connection was closed
            mock_connection.close.assert_called_once()

    @patch("scout.integration.anvil_bridge.DatabaseManager")
    def test_sync_ci_run_verbose_output(self, mock_db_manager):
        """Test verbose output during sync."""
        from datetime import datetime

        # Mock workflow run
        mock_run = Mock()
        mock_run.run_id = 123
        mock_run.workflow_name = "Test"
        mock_run.started_at = datetime(2026, 2, 1, 10, 0)
        mock_run.commit_sha = "abc"
        mock_run.branch = "main"
        mock_run.conclusion = "success"
        mock_run.duration_seconds = 100

        # Mock job with tests
        mock_job = Mock()
        mock_job.job_id = 1
        mock_job.job_name = "test-job"
        mock_job.runner_os = "ubuntu-latest"

        mock_test = Mock()
        mock_test.test_nodeid = "tests/test.py::test_func"
        mock_test.outcome = "passed"
        mock_test.duration = 1.0
        mock_test.error_message = None

        # Mock session
        mock_session = Mock()

        from scout.storage.schema import WorkflowJob, WorkflowRun, WorkflowTestResult

        def query_side_effect(model):
            if model == WorkflowRun:
                result = Mock()
                result.filter_by.return_value.first.return_value = mock_run
                return result
            elif model == WorkflowJob:
                result = Mock()
                result.filter_by.return_value.all.return_value = [mock_job]
                return result
            elif model == WorkflowTestResult:
                result = Mock()
                result.filter_by.return_value.all.return_value = [mock_test]
                return result
            return Mock()

        mock_session.query = Mock(side_effect=query_side_effect)
        mock_db_manager.return_value.get_session.return_value = mock_session

        # Mock Anvil
        mock_anvil_db = Mock()
        mock_anvil_db.insert_validation_run.return_value = 999
        mock_stats_db_class = Mock(return_value=mock_anvil_db)

        mock_validation_run = Mock()
        mock_test_case_record = Mock()

        mock_anvil_module = Mock()
        mock_anvil_module.StatisticsDatabase = mock_stats_db_class
        mock_anvil_module.ValidationRun = mock_validation_run
        mock_anvil_module.TestCaseRecord = mock_test_case_record

        with patch.dict("sys.modules", {"anvil.storage.statistics_database": mock_anvil_module}):
            bridge = AnvilBridge("scout.db", "anvil.db")

            # Capture print output
            import io
            import sys

            captured_output = io.StringIO()
            sys.stdout = captured_output

            result = bridge.sync_ci_run_to_anvil(123, verbose=True)

            sys.stdout = sys.__stdout__

            # Verify verbose output
            output = captured_output.getvalue()
            assert "Created Anvil validation run" in output
            assert "Processing job test-job" in output
            assert "Synced 1 tests from 1 jobs" in output

            assert result["tests_synced"] == 1
